# Copyright 2013-Today Odoo SA
# Copyright 2019-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import re

from odoo.exceptions import UserError
from odoo.tests.common import Form

from odoo.addons.account_invoice_inter_company.tests.test_inter_company_invoice import (
    TestAccountInvoiceInterCompanyBase,
)


class TestPurchaseSaleInterCompany(TestAccountInvoiceInterCompanyBase):
    @classmethod
    def _create_warehouse(cls, code, company):
        address = cls.env["res.partner"].create({"name": f"{code} address"})
        return cls.env["stock.warehouse"].create(
            {
                "name": f"Warehouse {code}",
                "code": code,
                "partner_id": address.id,
                "company_id": company.id,
            }
        )

    @classmethod
    def _configure_user(cls, user):
        for xml in [
            "account.group_account_manager",
            "base.group_partner_manager",
            "sales_team.group_sale_manager",
            "purchase.group_purchase_manager",
        ]:
            user.groups_id |= cls.env.ref(xml)

    @classmethod
    def _create_purchase_order(cls, partner, product_ids=None):
        if not product_ids:
            product_ids = [None]

        po = Form(cls.env["purchase.order"])
        po.company_id = cls.company_a
        po.partner_id = partner

        cls.product.invoice_policy = "order"

        for product_id in product_ids:
            with po.order_line.new() as line_form:
                line_form.product_id = product_id or cls.product
                line_form.product_qty = 3.0
                line_form.price_unit = 450.0
        return po.save()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lot_obj = cls.env["stock.production.lot"]
        cls.quant_obj = cls.env["stock.quant"]
        # no job: avoid issue if account_invoice_inter_company_queued is installed
        cls.env = cls.env(context={"test_queue_job_no_delay": 1})

        cls.product = cls.product_consultant_multi_company

        cls.consumable_product = cls.env["product.product"].create(
            {
                "name": "Consumable Product",
                "type": "consu",
                "categ_id": cls.env.ref("product.product_category_all").id,
                "qty_available": 100,
            }
        )
        cls.consumable_product_2 = cls.env["product.product"].create(
            {
                "name": "Consumable Product 2",
                "type": "consu",
            }
        )
        cls.stockable_product_serial = cls.env["product.product"].create(
            {
                "name": "Stockable Product Tracked by Serial",
                "type": "product",
                "tracking": "serial",
                "categ_id": cls.env.ref("product.product_category_all").id,
            }
        )

        # if partner_multi_company or product_multi_company is installed
        # We have to do that because the default method added a company
        if "company_ids" in cls.env["res.partner"]._fields:
            cls.partner_company_a.company_ids = False
            cls.partner_company_b.company_ids = False

        if "company_ids" in cls.env["product.template"]._fields:
            cls.product.company_ids = False
            cls.consumable_product.company_ids = False

        # Configure 2 Warehouse per company
        cls.warehouse_a = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company_a.id)]
        )
        cls.warehouse_b = cls._create_warehouse("CA-WB", cls.company_a)

        cls.warehouse_c = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company_b.id)]
        )
        cls.warehouse_d = cls._create_warehouse("CB-WD", cls.company_b)

        # Configure Company B (the supplier)
        cls.company_b.so_from_po = True
        cls.company_b.warehouse_id = cls.warehouse_c
        cls.company_b.sale_auto_validation = 1

        cls.intercompany_sale_user_id = cls.user_company_b.copy()
        cls.intercompany_sale_user_id.company_ids |= cls.company_a
        cls.company_b.intercompany_sale_user_id = cls.intercompany_sale_user_id

        # Configure User
        cls._configure_user(cls.user_company_a)
        cls._configure_user(cls.user_company_b)

        # Create purchase order
        cls.purchase_company_a = cls._create_purchase_order(cls.partner_company_b)

        # Configure pricelist to USD
        cls.env["product.pricelist"].sudo().search([]).write(
            {"currency_id": cls.env.ref("base.USD").id}
        )

        # Add quants for product tracked by serial to supplier
        cls.serial_1 = cls._create_serial_and_quant(
            cls.stockable_product_serial, "111", cls.company_b
        )
        cls.serial_2 = cls._create_serial_and_quant(
            cls.stockable_product_serial, "222", cls.company_b
        )
        cls.serial_3 = cls._create_serial_and_quant(
            cls.stockable_product_serial, "333", cls.company_b
        )

    @classmethod
    def _create_serial_and_quant(cls, product, name, company, quant=True):
        lot = cls.lot_obj.create(
            {"product_id": product.id, "name": name, "company_id": company.id}
        )
        if quant:
            cls.quant_obj.create(
                {
                    "product_id": product.id,
                    "location_id": cls.warehouse_a.lot_stock_id.id,
                    "quantity": 1,
                    "lot_id": lot.id,
                }
            )
        return lot

    def create_picking(self, product_id=None, location_id=None, location_dest_id=None):
        product_id = product_id or self.env.ref("product.product_product_8")
        location_id = location_id or self.env.ref("stock.stock_location_stock")
        location_dest_id = location_dest_id or self.env.ref(
            "stock.stock_location_customers"
        )

        picking_data = {
            "partner_id": self.company_a.partner_id.id,
            "picking_type_id": self.env.ref("stock.picking_type_out").id,
            "location_id": location_id.id,
            "location_dest_id": location_dest_id.id,
            "move_lines": [
                (
                    0,
                    0,
                    {
                        "name": product_id.name,
                        "product_id": product_id.id,
                        "product_uom_qty": 3,
                        "product_uom": product_id.uom_id.id,
                        "location_id": location_id.id,
                        "location_dest_id": location_dest_id.id,
                    },
                )
            ],
        }

        return self.env["stock.picking"].create(picking_data)

    def _approve_po(self, purchase_id):
        """Confirm the PO in company A and return the related sale of Company B"""

        purchase_id.with_user(self.intercompany_sale_user_id).button_approve()

        return (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", purchase_id.id)])
        )

    def test_purchase_sale_inter_company(self):
        self.purchase_company_a.notes = "Test note"
        sale = self._approve_po(self.purchase_company_a)
        self.assertEqual(len(sale), 1)
        self.assertEqual(sale.state, "sale")
        self.assertEqual(sale.partner_id, self.partner_company_a)
        self.assertEqual(len(sale.order_line), len(self.purchase_company_a.order_line))
        self.assertEqual(sale.order_line.product_id, self.product)
        self.assertEqual(sale.note, "Test note")

    def test_not_auto_validate(self):
        self.company_b.sale_auto_validation = False
        sale = self._approve_po(self.purchase_company_a)
        self.assertEqual(sale.state, "draft")

    def test_deliver_to_warehouse_a(self):
        self.purchase_company_a.picking_type_id = self.warehouse_a.in_type_id
        sale = self._approve_po(self.purchase_company_a)
        self.assertEqual(self.warehouse_a.partner_id, sale.partner_shipping_id)

    def test_deliver_to_warehouse_b(self):
        self.purchase_company_a.picking_type_id = self.warehouse_b.in_type_id
        sale = self._approve_po(self.purchase_company_a)
        self.assertEqual(self.warehouse_b.partner_id, sale.partner_shipping_id)

    def test_send_from_warehouse_c(self):
        self.company_b.warehouse_id = self.warehouse_c
        sale = self._approve_po(self.purchase_company_a)
        self.assertEqual(sale.warehouse_id, self.warehouse_c)

    def test_send_from_warehouse_d(self):
        self.company_b.warehouse_id = self.warehouse_d
        sale = self._approve_po(self.purchase_company_a)
        self.assertEqual(sale.warehouse_id, self.warehouse_d)

    # TODO FIXME
    def xxtest_date_planned(self):
        # Install sale_order_dates module
        module = self.env["ir.module.module"].search(
            [("name", "=", "sale_order_dates")]
        )
        if not module:
            return False
        module.button_install()
        self.purchase_company_a.date_planned = "2070-12-31"
        sale = self._approve_po(self.purchase_company_a)
        self.assertEqual(sale.requested_date, "2070-12-31")

    def test_raise_product_access(self):
        product_rule = self.env.ref("product.product_comp_rule")
        product_rule.active = True
        # if product_multi_company is installed
        if "company_ids" in self.env["product.template"]._fields:
            self.product.company_ids = [(6, 0, [self.company_a.id])]
        self.product.company_id = self.company_a
        with self.assertRaises(UserError):
            self._approve_po(self.purchase_company_a)

    def test_raise_currency(self):
        currency = self.env.ref("base.EUR")
        self.purchase_company_a.currency_id = currency
        with self.assertRaises(UserError):
            self._approve_po(self.purchase_company_a)

    def test_purchase_invoice_relation(self):
        self.partner_company_a.company_id = False
        self.partner_company_b.company_id = False
        sale = self._approve_po(self.purchase_company_a)
        sale_invoice = sale._create_invoices()[0]
        sale_invoice.action_post()
        self.assertEqual(len(self.purchase_company_a.invoice_ids), 1)
        self.assertEqual(
            self.purchase_company_a.invoice_ids.auto_invoice_id,
            sale_invoice,
        )
        self.assertEqual(len(self.purchase_company_a.order_line.invoice_lines), 1)
        self.assertEqual(self.purchase_company_a.order_line.qty_invoiced, 3)

    def test_cancel(self):
        self.company_b.sale_auto_validation = False
        sale = self._approve_po(self.purchase_company_a)
        self.assertEqual(self.purchase_company_a.partner_ref, sale.name)
        self.purchase_company_a.with_user(self.user_company_a).button_cancel()
        self.assertFalse(self.purchase_company_a.partner_ref)
        self.assertEqual(sale.state, "cancel")

    def test_cancel_confirmed_po_so(self):
        self.company_b.sale_auto_validation = True
        self._approve_po(self.purchase_company_a)
        with self.assertRaises(UserError):
            self.purchase_company_a.with_user(self.user_company_a).button_cancel()

    def test_so_change_price(self):
        sale = self._approve_po(self.purchase_company_a)
        sale.order_line.price_unit = 10
        sale.action_confirm()
        self.assertEqual(self.purchase_company_a.order_line.price_unit, 10)

    def test_po_with_contact_as_partner(self):
        contact = self.env["res.partner"].create(
            {"name": "Test contact", "parent_id": self.partner_company_b.id}
        )
        self.purchase_company_a = self._create_purchase_order(contact)
        sale = self._approve_po(self.purchase_company_a)
        self.assertEqual(len(sale), 1)
        self.assertEqual(sale.state, "sale")
        self.assertEqual(sale.partner_id, self.partner_company_a)

    def test_confirm_several_picking(self):
        """
        Ensure that confirming several picking is not broken
        """
        purchase_1 = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        purchase_2 = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        sale_1 = self._approve_po(purchase_1)
        sale_2 = self._approve_po(purchase_2)
        pickings = sale_1.picking_ids | sale_2.picking_ids
        for move in pickings.move_lines:
            move.quantity_done = move.product_uom_qty
        pickings.button_validate()
        self.assertEqual(pickings.mapped("state"), ["done", "done"])

    def test_sync_picking(self):
        self.company_a.sync_picking = True
        self.company_b.sync_picking = True

        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        sale = self._approve_po(purchase)

        self.assertTrue(purchase.picking_ids)
        self.assertTrue(sale.picking_ids)

        po_picking_id = purchase.picking_ids
        so_picking_id = sale.picking_ids

        # check po_picking state
        self.assertEqual(po_picking_id.state, "waiting")

        # validate the SO picking
        so_picking_id.move_lines.quantity_done = 2

        self.assertNotEqual(po_picking_id, so_picking_id)
        self.assertNotEqual(
            po_picking_id.move_lines.quantity_done,
            so_picking_id.move_lines.quantity_done,
        )
        self.assertEqual(
            po_picking_id.move_lines.product_qty,
            so_picking_id.move_lines.product_qty,
        )

        so_picking_id.state = "done"
        wizard_data = so_picking_id.with_user(self.user_company_b).button_validate()
        wizard = (
            self.env["stock.backorder.confirmation"]
            .with_context(**wizard_data.get("context"))
            .create({})
        )
        wizard.process()

        # Quantities should have been synced
        self.assertNotEqual(po_picking_id, so_picking_id)
        self.assertEqual(
            po_picking_id.move_lines.quantity_done,
            so_picking_id.move_lines.quantity_done,
        )

        # Check picking state
        self.assertEqual(po_picking_id.state, so_picking_id.state)

        # A backorder should have been made for both
        self.assertTrue(len(sale.picking_ids) > 1)
        self.assertEqual(len(purchase.picking_ids), len(sale.picking_ids))

    def test_sync_picking_no_backorder(self):
        self.company_a.sync_picking = True
        self.company_b.sync_picking = True

        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        sale = self._approve_po(purchase)

        self.assertTrue(purchase.picking_ids)
        self.assertTrue(sale.picking_ids)

        po_picking_id = purchase.picking_ids
        so_picking_id = sale.picking_ids

        # check po_picking state
        self.assertEqual(po_picking_id.state, "waiting")

        # validate the SO picking
        so_picking_id.move_lines.quantity_done = 2

        self.assertNotEqual(po_picking_id, so_picking_id)
        self.assertNotEqual(
            po_picking_id.move_lines.quantity_done,
            so_picking_id.move_lines.quantity_done,
        )
        self.assertEqual(
            po_picking_id.move_lines.product_qty,
            so_picking_id.move_lines.product_qty,
        )

        # No backorder
        wizard_data = so_picking_id.with_user(self.user_company_b).button_validate()
        wizard = (
            self.env["stock.backorder.confirmation"]
            .with_context(**wizard_data.get("context"))
            .create({})
        )
        wizard.with_user(self.user_company_b).process_cancel_backorder()
        self.assertEqual(so_picking_id.state, "done")
        self.assertEqual(po_picking_id.state, "done")

        # Quantity done should be the same on both sides, per product
        self.assertNotEqual(po_picking_id, so_picking_id)
        for product in so_picking_id.move_lines.mapped("product_id"):
            self.assertEqual(
                sum(
                    so_picking_id.move_lines.filtered(
                        lambda l: l.product_id == product
                    ).mapped("quantity_done")
                ),
                sum(
                    po_picking_id.move_lines.filtered(
                        lambda l: l.product_id == product
                    ).mapped("quantity_done")
                ),
            )

        # No backorder should have been made for both
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(len(purchase.picking_ids), len(sale.picking_ids))

    def test_sync_picking_lot(self):
        """
        Test that the lot is synchronized on the moves
        by searching or creating a new lot in the company of destination
        """
        # lot 3 already exists in company_a
        serial_3_company_a = self._create_serial_and_quant(
            self.stockable_product_serial,
            "333",
            self.company_a,
            quant=False,
        )
        self.company_a.sync_picking = True
        self.company_b.sync_picking = True

        purchase = self._create_purchase_order(
            self.partner_company_b, self.stockable_product_serial
        )
        sale = self._approve_po(purchase)

        # validate the SO picking
        po_picking_id = purchase.picking_ids
        so_picking_id = sale.picking_ids

        so_move = so_picking_id.move_lines
        so_move.move_line_ids = [
            (
                0,
                0,
                {
                    "location_id": so_move.location_id.id,
                    "location_dest_id": so_move.location_dest_id.id,
                    "product_id": self.stockable_product_serial.id,
                    "product_uom_id": self.stockable_product_serial.uom_id.id,
                    "qty_done": 1,
                    "lot_id": self.serial_1.id,
                    "picking_id": so_picking_id.id,
                },
            ),
            (
                0,
                0,
                {
                    "location_id": so_move.location_id.id,
                    "location_dest_id": so_move.location_dest_id.id,
                    "product_id": self.stockable_product_serial.id,
                    "product_uom_id": self.stockable_product_serial.uom_id.id,
                    "qty_done": 1,
                    "lot_id": self.serial_2.id,
                    "picking_id": so_picking_id.id,
                },
            ),
            (
                0,
                0,
                {
                    "location_id": so_move.location_id.id,
                    "location_dest_id": so_move.location_dest_id.id,
                    "product_id": self.stockable_product_serial.id,
                    "product_uom_id": self.stockable_product_serial.uom_id.id,
                    "qty_done": 1,
                    "lot_id": self.serial_3.id,
                    "picking_id": so_picking_id.id,
                },
            ),
        ]
        so_picking_id.button_validate()

        so_lots = so_move.mapped("move_line_ids.lot_id")
        po_lots = po_picking_id.mapped("move_lines.move_line_ids.lot_id")
        self.assertEqual(
            len(so_lots),
            len(po_lots),
            msg="There aren't the same number of lots on both moves",
        )
        self.assertNotEqual(
            so_lots, po_lots, msg="The lots of the moves should be different objects"
        )
        self.assertEqual(
            so_lots.mapped("name"),
            po_lots.mapped("name"),
            msg="The lots should have the same name in both moves",
        )
        self.assertIn(
            serial_3_company_a,
            po_lots,
            msg="Serial 333 already existed, a new one shouldn't have been created",
        )

    def test_sync_picking_same_product_multiple_lines(self):
        """
        Picking synchronization should work even when there
        are multiple lines of the same product in the PO/SO/picking
        """
        self.company_a.sync_picking = True
        self.company_b.sync_picking = True

        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        purchase.order_line += purchase.order_line.copy({"product_qty": 2})
        sale = self._approve_po(purchase)
        sale.action_confirm()

        # validate the SO picking
        po_picking_id = purchase.picking_ids
        so_picking_id = sale.picking_ids

        # Set quantities done on the picking and validate
        for move in so_picking_id.move_lines:
            move.quantity_done = move.product_uom_qty
        so_picking_id.button_validate()

        self.assertEqual(
            po_picking_id.mapped("move_lines.quantity_done"),
            so_picking_id.mapped("move_lines.quantity_done"),
            msg="The quantities are not the same in both pickings.",
        )

    def test_sync_picking_different_product_multiple_lines(self):
        """
        Test that the action_confirm of the sale order
        still works even if the amount of pickings is
        different between the sale order and the purchase order
        """

        self.company_a.sync_picking = True
        self.company_b.sync_picking = True

        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product | self.consumable_product_2
        )
        sale = self._approve_po(purchase)

        new_picking = self.create_picking(
            product_id=self.consumable_product_2,
            location_id=sale.picking_ids.location_id,
            location_dest_id=sale.picking_ids.location_dest_id,
        )
        sale.sudo().write({"picking_ids": [(4, new_picking.id)]})
        sale.action_confirm()

    def test_update_open_sale_order(self):
        """
        When the purchase user request extra product, the sale order gets synched if
        it's open.
        """
        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        purchase.picking_type_id = self.warehouse_a.in_type_id
        sale = self._approve_po(purchase)
        sale.action_confirm()
        # Now we add an extra product to the PO and it will show up in the SO
        po_form = Form(purchase)
        with po_form.order_line.new() as line:
            line.product_id = self.consumable_product_2
            line.product_qty = 6
        po_form.save()
        # It's synched and the values match
        synched_order_line = sale.order_line.filtered(
            lambda x: x.product_id == self.consumable_product_2
        )
        self.assertTrue(
            bool(synched_order_line),
            "The line should have been created in the sale order",
        )
        self.assertEqual(
            synched_order_line.product_uom_qty,
            6,
            "The quantity should be equal to the one set in the purchase order",
        )
        # Also the moves match as well
        so_picking_id = sale.picking_ids
        synched_move = so_picking_id.move_lines.filtered(
            lambda x: x.product_id == self.consumable_product_2
        )
        self.assertTrue(
            bool(synched_move),
            "The move should have been created in the delivery order",
        )
        self.assertEqual(
            synched_move.product_uom_qty,
            6,
            "The quantity should be equal to the one set in the purchase order",
        )
        # The quantity is synched as well
        purchase_line = purchase.order_line.filtered(
            lambda x: x.product_id == self.consumable_product_2
        ).sudo()
        purchase_line.product_qty = 8
        self.assertEqual(
            synched_order_line.product_uom_qty,
            8,
            "The quantity should be equal to the one set in the purchase order",
        )
        self.assertEqual(
            synched_move.product_uom_qty,
            8,
            "The quantity should synched to the one set in the purchase order",
        )
        # Let's decrease the quantity
        purchase_line.product_qty = 3
        self.assertEqual(
            synched_order_line.product_uom_qty,
            3,
            "The quantity should decrease as it was in the purchase order",
        )
        self.assertEqual(
            synched_move.product_uom_qty,
            8,
            "The quantity should remain as it was as it can't be decreased from the SO",
        )
        # A warning activity is scheduled in the picking
        self.assertRegex(
            so_picking_id.activity_ids.note,
            re.compile(
                "3.0 Units of Consumable Product 2.+instead of 8.0 Units", re.DOTALL
            ),
        )

    def test_block_manual_validation(self):
        """
        Test that the manual validation of the picking is blocked
        when the flag is set in the destination company
        """
        self.company_a.sync_picking = True
        self.company_b.sync_picking = True
        self.company_a.block_po_manual_picking_validation = True
        self.company_b.block_po_manual_picking_validation = True
        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        purchase.button_confirm()
        po_picking_id = purchase.picking_ids
        # The picking should be in waiting state
        self.assertEqual(po_picking_id.state, "waiting")
        # The manual validation should be blocked
        with self.assertRaises(UserError):
            po_picking_id.with_user(self.user_company_a).button_validate()

    def test_notify_picking_problem(self):
        self.company_a.sync_picking = True
        self.company_b.sync_picking = True
        self.company_a.sync_picking_failure_action = "notify"
        self.company_b.sync_picking_failure_action = "notify"
        self.company_a.notify_user_id = self.user_company_a
        self.company_b.notify_user_id = self.user_company_b

        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        purchase_2 = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        purchase.order_line += purchase.order_line.copy({"product_qty": 2})
        sale = self._approve_po(purchase)
        sale.action_confirm()

        # validate the SO picking
        so_picking_id = sale.picking_ids

        # Link to a new purchase order so it can trigger
        # `PO does not exist or has no receipts` in _sync_receipt_with_delivery
        sale.auto_purchase_order_id = purchase_2

        # Set quantities done on the picking and validate
        for move in so_picking_id.move_lines:
            move.quantity_done = move.product_uom_qty
        so_picking_id.button_validate()

        # Test that picking has an activity now
        self.assertTrue(len(so_picking_id.activity_ids) > 0)
        activity_warning = self.env.ref("mail.mail_activity_data_warning")
        warning_activity = so_picking_id.activity_ids.filtered(
            lambda a: a.activity_type_id == activity_warning
        )
        self.assertEqual(len(warning_activity), 1)

        # Test the user assigned to the activity
        self.assertEqual(
            warning_activity.user_id, so_picking_id.company_id.notify_user_id
        )

    def test_raise_picking_problem(self):
        self.company_a.sync_picking = True
        self.company_b.sync_picking = True
        self.company_a.sync_picking_failure_action = "raise"
        self.company_b.sync_picking_failure_action = "raise"

        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        purchase_2 = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        purchase.order_line += purchase.order_line.copy({"product_qty": 2})
        sale = self._approve_po(purchase)
        sale.action_confirm()

        # validate the SO picking
        so_picking_id = sale.picking_ids

        # Link to a new purchase order so it can trigger
        # `PO does not exist or has no receipts` in _sync_receipt_with_delivery
        sale.auto_purchase_order_id = purchase_2

        # Set quantities done on the picking and validate
        for move in so_picking_id.move_lines:
            move.quantity_done = move.product_uom_qty
        with self.assertRaises(UserError):
            so_picking_id.button_validate()
