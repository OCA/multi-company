# Copyright 2023 Camptocamp (<https://www.camptocamp.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.exceptions import UserError
from odoo.tests.common import Form

from odoo.addons.account_invoice_inter_company.tests.test_inter_company_invoice import (
    TestAccountInvoiceInterCompanyBase,
)
from odoo.addons.product_packaging_container_deposit.tests.common import (
    Common as ProductPackagingContainerDepositCommon,
)


class TestProductPackagingContainerDepositMixin(
    ProductPackagingContainerDepositCommon, TestAccountInvoiceInterCompanyBase
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # no job: avoid issue if account_invoice_inter_company_queued is installed
        cls.env = cls.env(context={"test_queue_job_no_delay": 1})

        # Ensure access right to Stock
        # To update the `update_order_container_deposit_quantity()`
        cls.user_company_a.groups_id += cls.env.ref("stock.group_stock_user")
        # Configure Company B (the supplier)
        cls.company_b.so_from_po = True
        cls.company_b.sale_auto_validation = 1
        # Configure pricelist to USD
        cls.env["product.pricelist"].sudo().search([]).write(
            {"currency_id": cls.env.ref("base.USD").id}
        )

        cls.intercompany_sale_user_id = cls.user_company_b.copy()
        cls.intercompany_sale_user_id.company_ids |= cls.company_a
        cls.company_b.intercompany_sale_user_id = cls.intercompany_sale_user_id

    @classmethod
    def _create_purchase_order_with_product_container_deposit(cls, partner):
        po = Form(cls.env["purchase.order"])
        po.company_id = cls.company_a
        po.partner_id = partner

        cls.product_a.invoice_policy = "order"

        with po.order_line.new() as line_form:
            line_form.product_id = cls.product_a
            line_form.product_qty = 280
        return po.save()

    @classmethod
    def _create_purchase_order_without_product_container_deposit(cls, partner):
        po = Form(
            cls.env["purchase.order"].with_context(skip_update_container_deposit=True)
        )
        po.company_id = cls.company_a
        po.partner_id = partner

        cls.product_a.invoice_policy = "order"

        with po.order_line.new() as line_form:
            line_form.product_id = cls.product_a
            line_form.product_qty = 280
        return po.save()

    def test_purchase_sale_product_container_deposit_inter_company(self):
        purchase = self._create_purchase_order_with_product_container_deposit(
            self.partner_company_b
        )
        purchase.with_user(self.user_company_a).button_approve()
        sale = (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", purchase.id)])
        )
        # PO product packaging container deposit quantities
        po_pallet_line = purchase.order_line.filtered(
            lambda ol: ol.product_id == self.pallet
        )
        po_box_line = purchase.order_line.filtered(lambda ol: ol.product_id == self.box)
        # SO product packaging container deposit quantities
        so_pallet_line = sale.order_line.filtered(
            lambda ol: ol.product_id == self.pallet
        )
        so_box_line = sale.order_line.filtered(lambda ol: ol.product_id == self.box)
        self.assertEqual(po_pallet_line.product_qty, so_pallet_line.product_uom_qty)
        self.assertEqual(po_box_line.product_qty, so_box_line.product_uom_qty)

    def test_purchase_locked_sale_product_container_deposit_inter_company(self):
        self.intercompany_sale_user_id.groups_id += self.env.ref(
            "sale.group_auto_done_setting"
        )
        purchase = self._create_purchase_order_without_product_container_deposit(
            self.partner_company_b
        )
        # Purchase Order doesn't have product container deposit
        self.assertEqual(len(purchase.order_line), 1)
        purchase.with_user(self.user_company_a).button_approve()
        sale = (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", purchase.id)])
        )
        # Now, the Sale Order is in Locked state
        self.assertEqual(sale.state, "done")
        # Sale Order doesn't have product container deposit too
        self.assertEqual(len(purchase.order_line), 1)
        # We can't write product qty on purchase order because the sale order is locked
        with self.assertRaisesRegex(
            UserError,
            f"The generated sale orders with reference {sale.name} can't be "
            "modified. They're either unconfirmed or locked for modifications.",
        ):
            purchase.order_line[0].write({"product_qty": 99})
        # With the "update_order_container_deposit_quantity" context
        # We can update order container deposit quantity on PO and locked SO also
        purchase.with_context(
            skip_update_container_deposit=False
        ).update_order_container_deposit_quantity()
        # PO product packaging container deposit quantities
        po_pallet_line = purchase.order_line.filtered(
            lambda ol: ol.product_id == self.pallet
        )
        po_box_line = purchase.order_line.filtered(lambda ol: ol.product_id == self.box)
        # SO product packaging container deposit quantities
        so_pallet_line = sale.order_line.filtered(
            lambda ol: ol.product_id == self.pallet
        )
        so_box_line = sale.order_line.filtered(lambda ol: ol.product_id == self.box)
        self.assertEqual(po_pallet_line.product_qty, so_pallet_line.product_uom_qty)
        self.assertEqual(po_box_line.product_qty, so_box_line.product_uom_qty)
