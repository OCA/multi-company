# Copyright 2022 Akretion
# @author Florian Mounier <florian.mounier@akretion.com>
# @author Guillaume MASSON <guillaume.masson@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.purchase_sale_stock_inter_company.tests import (
    test_inter_company_purchase_sale_stock as test_icpss,
)

TestPurchaseSaleStockInterCompany = test_icpss.TestPurchaseSaleStockInterCompany


@tagged("post_install", "-at_install")
class TestGluePurchaseSaleStockIntercompany(TestPurchaseSaleStockInterCompany):
    """Test compatibility between purchase_sale_stock_inter_company and
    stock_intercompany when both modules are installed together.

    This class extends the purchase_sale_stock_inter_company test suite so that
    all existing tests run with stock_intercompany active, verifying that the
    glue module prevents any interference in both directions (LR and RL).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Configure stock_intercompany on both companies in "Create Both" mode
        # so that it would normally create counterpart pickings in both directions
        # on its own — the glue module must neutralise this when the PO/SO flow
        # is already managing the picking.
        cls.company_a.intercompany_in_type_id = cls.warehouse_a.in_type_id
        cls.company_a.intercompany_out_type_id = cls.warehouse_a.out_type_id
        cls.company_a.intercompany_picking_creation_mode = "both"
        cls.company_b.intercompany_in_type_id = cls.warehouse_c.in_type_id
        cls.company_b.intercompany_out_type_id = cls.warehouse_c.out_type_id
        cls.company_b.intercompany_picking_creation_mode = "both"

    # -------------------------------------------------------------------------
    # LR direction: delivery in vendor company → receipt in buyer company
    # -------------------------------------------------------------------------

    def test_no_duplicate_receipt_with_so_from_po(self):
        """When so_from_po is enabled, purchase_sale_stock_inter_company manages
        the receipt in company_a via the PO/SO pair.  stock_intercompany must
        not create an additional receipt, leaving exactly one receipt per side.

        so_from_po and sale_auto_validation are already True from the parent
        setUpClass; only sync_picking needs to be enabled here so that
        purchase_sale_stock_inter_company actually validates the receipt upon
        delivery, making the duplicate risk concrete.
        """
        self.company_b.sync_picking = True

        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        sale = self._approve_po(purchase)

        # Company B (vendor): exactly one delivery
        self.assertEqual(len(sale.picking_ids), 1)
        so_picking = sale.picking_ids
        self.assertEqual(so_picking.state, "assigned")

        # Validate the delivery in company B
        so_picking.with_user(self.user_company_b).button_validate()
        self.assertEqual(so_picking.state, "done")

        # Company A (buyer): exactly one receipt — no duplicate from stock_intercompany.
        self.assertEqual(
            len(purchase.picking_ids),
            1,
            "stock_intercompany must not create a duplicate receipt "
            "when purchase_sale_stock_inter_company already handles it.",
        )
        po_picking = purchase.picking_ids
        # The receipt must be the one managed by purchase_sale_stock_inter_company,
        # linked to the SO delivery via intercompany_picking_id — not a standalone
        # orphan created by stock_intercompany.
        self.assertTrue(
            po_picking.intercompany_picking_id,
            "The receipt in company A must be linked to the SO delivery "
            "via intercompany_picking_id.",
        )
        # stock_intercompany must not have added its own intercompany_parent_id.
        self.assertFalse(
            po_picking.intercompany_parent_id,
            "The receipt must not have an intercompany_parent_id: "
            "it was created by purchase_sale_stock_inter_company, "
            "not stock_intercompany.",
        )

    # -------------------------------------------------------------------------
    # RL direction: receipt in buyer company → delivery in vendor company
    # -------------------------------------------------------------------------

    def test_no_counterpart_delivery_for_po_intercompany_receipt(self):
        """When a receipt in company_a is linked to an inter-company PO
        (intercompany_sale_order_id is set), stock_intercompany must not create
        a delivery counterpart in company_b — that relationship is already
        expressed by the PO/SO document pair.

        This test uses the manual 'Create Counterpart' action to simulate what
        would happen if a user or the scheduled action tried to create an 'out'
        counterpart on a managed picking.
        """
        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        self._approve_po(purchase)

        # The receipt in company A is already linked to the PO.
        po_picking = purchase.picking_ids
        self.assertTrue(po_picking)
        self.assertTrue(po_picking.purchase_id.sudo().intercompany_sale_order_id)

        # Attempt to create an 'out' counterpart via the stock_intercompany action.
        po_picking.action_create_counterpart()

        # No delivery must have been created in company B by stock_intercompany.
        self.assertFalse(
            po_picking.has_counterpart,
            "stock_intercompany must not create a delivery counterpart "
            "for a receipt that is already managed by "
            "purchase_sale_stock_inter_company.",
        )

    def test_cron_excludes_po_intercompany_receipts(self):
        """The stock_intercompany scheduled action domain must exclude reception
        pickings that are linked to an inter-company PO, so the cron never
        creates spurious delivery counterparts for them."""
        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        self._approve_po(purchase)

        po_picking = purchase.picking_ids
        self.assertTrue(po_picking)
        self.assertTrue(po_picking.purchase_id.sudo().intercompany_sale_order_id)

        remaining = self.env["stock.picking"]._remaining_out_counterpart_picking()
        self.assertNotIn(
            po_picking,
            remaining,
            "A receipt linked to an inter-company PO must be excluded "
            "from the stock_intercompany scheduled action domain.",
        )

    def test_no_duplicate_receipt_without_so_from_po(self):
        """When so_from_po is disabled, purchase_sale_stock_inter_company does
        not create a SO and does not manage any receipt.  stock_intercompany
        must still create its counterpart receipt normally in mode 'in'."""
        self.company_b.so_from_po = False

        # Create a manual delivery in company B toward company A partner
        # (no PO/SO pair involved).
        picking = (
            self.env["stock.picking"]
            .with_company(self.company_b)
            .sudo()
            .create(
                {
                    "partner_id": self.partner_company_a.id,
                    "picking_type_id": self.warehouse_c.out_type_id.id,
                    "location_id": self.warehouse_c.lot_stock_id.id,
                    "location_dest_id": self.env.ref(
                        "stock.stock_location_customers"
                    ).id,
                }
            )
        )
        self.env["stock.move"].with_company(self.company_b).sudo().create(
            {
                "name": self.consumable_product.name,
                "product_id": self.consumable_product.id,
                "product_uom_qty": 2.0,
                "product_uom": self.consumable_product.uom_id.id,
                "picking_id": picking.id,
                "location_id": self.warehouse_c.lot_stock_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.sudo().button_validate()
        self.assertEqual(picking.state, "done")

        # stock_intercompany must have created exactly one receipt in company A.
        counterpart = (
            self.env["stock.picking"]
            .sudo()
            .search(
                [
                    ("intercompany_parent_id", "=", picking.id),
                    ("company_id", "=", self.company_a.id),
                ]
            )
        )
        self.assertEqual(
            len(counterpart),
            1,
            "stock_intercompany must create one receipt in company A "
            "when no PO/SO pair manages the delivery.",
        )
