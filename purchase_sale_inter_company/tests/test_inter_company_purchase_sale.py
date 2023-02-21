# Copyright 2013-Today Odoo SA
# Copyright 2019-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import Form

from odoo.addons.account_invoice_inter_company.tests.test_inter_company_invoice import (
    TestAccountInvoiceInterCompanyBase,
)


class TestPurchaseSaleInterCompany(TestAccountInvoiceInterCompanyBase):
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
    def _create_purchase_order(cls, partner):
        po = Form(cls.env["purchase.order"])
        po.company_id = cls.company_a
        po.partner_id = partner

        cls.product.invoice_policy = "order"

        with po.order_line.new() as line_form:
            line_form.product_id = cls.product
            line_form.account_analytic_id = cls.analytic_account_sale
            line_form.product_qty = 3.0
            line_form.name = "Service Multi Company"
            line_form.price_unit = 450.0
        return po.save()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # no job: avoid issue if account_invoice_inter_company_queued is installed
        cls.env = cls.env(
            context=dict(
                cls.env.context, tracking_disable=True, test_queue_job_no_delay=1
            )
        )

        cls.product = cls.product_consultant_multi_company
        cls.analytic_account_sale = cls.env["account.analytic.account"].create(
            {"name": "Project for selling timesheet - AA1", "code": "AA-20301"}
        )

        if "company_ids" in cls.env["res.partner"]._fields:
            # We have to do that because the default method added a company
            cls.partner_company_a.company_ids = [(6, 0, cls.company_a.ids)]
            cls.partner_company_b.company_ids = [(6, 0, cls.company_b.ids)]

        # Configure Company B (the supplier)
        cls.company_b.so_from_po = True
        cls.company_b.sale_auto_validation = 1

        cls.intercompany_sale_user_id = cls.user_company_b.copy()
        cls.intercompany_sale_user_id.company_ids |= cls.company_a
        cls.company_b.intercompany_sale_user_id = cls.intercompany_sale_user_id

        # Configure User
        cls._configure_user(cls.user_company_a)
        cls._configure_user(cls.user_company_b)

        # Create purchase order
        cls.purchase_company_a = cls._create_purchase_order(cls.partner_company_b)
        cls.purchase_company_a.notes = "Test note"

        # Configure pricelist to EUR
        cls.env["product.pricelist"].sudo().search([]).write(
            {"currency_id": cls.env.ref("base.EUR").id}
        )
        cls.purchase_company_a_child = cls._create_purchase_order(cls.partner_company_b)
        cls.purchase_company_a_child.notes = "Test note child"
        cls.purchase_company_a_child.partner_id = cls.partner_company_b.child_ids

    def _approve_po(self, *args):
        """Confirm the PO in company A and return the related sale of Company B"""
        purchase_order = self.purchase_company_a
        if args:
            (purchase_order,) = args
        purchase_order.with_user(self.user_company_a).button_approve()
        return (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", purchase_order.id)])
        )

    def _set_ignore_exception(self, *args):
        # set ignore_exception=True to confirm the order
        # if purchase_exception module is installed
        purchase_order = self.purchase_company_a
        if args:
            (purchase_order,) = args
        if "ignore_exception" in self.env["purchase.order"]:
            purchase_order.ignore_exception = True

    def _check_inter_company_data(self, purchase_order):
        sale = self._approve_po(purchase_order)
        self.assertNotEqual(sale, False)
        self.assertEqual(len(sale), 1)
        if sale.company_id.sale_auto_validation:
            self.assertEqual(sale.state, "sale")
        else:
            self.assertEqual(sale.state, "draft")
        self.assertEqual(
            sale.partner_id,
            purchase_order.company_id.partner_id,
        )
        po_partner = purchase_order.partner_id

        if po_partner.ref_company_ids:
            vendor = po_partner.ref_company_ids
            self.assertEqual(sale.note, "<p>Test note</p>")
        if po_partner.parent_id.ref_company_ids:
            vendor = po_partner.parent_id.ref_company_ids
            self.assertEqual(sale.note, "<p>Test note child</p>")
        self.assertEqual(sale.company_id.partner_id, vendor.partner_id)
        self.assertEqual(len(sale.order_line), len(purchase_order.order_line))
        self.assertEqual(
            sale.order_line.product_id,
            purchase_order.order_line.product_id,
        )
        self.assertEqual(sale.currency_id, purchase_order.currency_id)

    def test_purchase_sale_inter_company(self):
        self._set_ignore_exception()
        self._check_inter_company_data(self.purchase_company_a)

        self._set_ignore_exception(self.purchase_company_a_child)
        self._check_inter_company_data(self.purchase_company_a_child)

    def test_purchase_sale_inter_company_pricelist(self):
        currency_usd = self.env.ref("base.USD")
        self.purchase_company_a.currency_id = currency_usd
        self._set_ignore_exception()
        self._check_inter_company_data(self.purchase_company_a)

        self.purchase_company_a_child.currency_id = self.env.ref("base.CHF")
        self._set_ignore_exception(self.purchase_company_a_child)
        self._check_inter_company_data(self.purchase_company_a_child)

    def test_not_auto_validate(self):
        self.company_b.sale_auto_validation = False
        self._set_ignore_exception()
        sale = self._approve_po()
        self.assertEqual(sale.state, "draft")

    def test_date_planned(self):
        # Install sale_order_dates module
        module = self.env["ir.module.module"].search(
            [("name", "=", "sale_order_dates")]
        )
        if not module:
            return False
        module.button_install()
        self.purchase_company_a.date_planned = "2070-12-31"
        self._set_ignore_exception()
        sale = self._approve_po()
        self.assertEqual(sale.requested_date, "2070-12-31")

    def test_raise_product_access(self):
        product_rule = self.env.ref("product.product_comp_rule")
        product_rule.active = True
        # if product_multi_company is installed
        if "company_ids" in self.env["product.template"]._fields:
            self.product.company_ids = [(6, 0, [self.company_a.id])]
        self.product.company_id = self.company_a
        with self.assertRaises(UserError):
            self._approve_po()

    def test_purchase_invoice_relation(self):
        self.partner_company_a.company_id = False
        self.partner_company_b.company_id = False
        self._set_ignore_exception()
        sale = self._approve_po()
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
        self._set_ignore_exception()
        sale = self._approve_po()
        self.assertEqual(self.purchase_company_a.partner_ref, sale.name)
        self.purchase_company_a.with_user(self.user_company_a).button_cancel()
        self.assertFalse(self.purchase_company_a.partner_ref)

    def test_so_change_price(self):
        self._set_ignore_exception()
        sale = self._approve_po()
        sale.order_line.price_unit = 10
        sale.action_confirm()
        self.assertEqual(self.purchase_company_a.order_line.price_unit, 10)

    def test_cancel_confirmed_po_so(self):
        self.company_b.sale_auto_validation = True
        self._set_ignore_exception()
        self._approve_po()
        with self.assertRaises(UserError):
            self.purchase_company_a.with_user(self.user_company_a).button_cancel()

    # def test_reconfirm_canceled_po_so(self):
    #     self.company_b.sale_auto_validation = True
    #     self._set_ignore_exception()
    #     self._approve_po()
    #     with self.assertRaises(UserError):
    #         self.purchase_company_a.with_user(self.user_company_a).button_cancel()
