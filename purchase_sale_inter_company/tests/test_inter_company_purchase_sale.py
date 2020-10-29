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
    def setUpClass(cls):
        super().setUpClass()

        cls.location_stock_company_a = cls.env["stock.location"].create(
            {"name": "Stock - a", "usage": "internal", "company_id": cls.company_a.id}
        )
        cls.location_output_company_a = cls.env["stock.location"].create(
            {"name": "Output - a", "usage": "internal", "company_id": cls.company_a.id}
        )
        if "company_ids" in cls.env["res.partner"]._fields:
            # We have to do that because the default method added a company
            cls.partner_company_a.company_ids = [(6, 0, cls.company_a.ids)]
            cls.partner_company_b.company_ids = [(6, 0, cls.company_b.ids)]
        cls.warehouse_company_a = cls.env["stock.warehouse"].create(
            {
                "name": "purchase warehouse - a",
                "code": "CMPa",
                "wh_input_stock_loc_id": cls.location_stock_company_a.id,
                "lot_stock_id": cls.location_stock_company_a.id,
                "wh_output_stock_loc_id": cls.location_output_company_a.id,
                "partner_id": cls.partner_company_a.id,
                "company_id": cls.company_a.id,
            }
        )
        cls.location_stock_company_b = cls.env["stock.location"].create(
            {"name": "Stock - b", "usage": "internal", "company_id": cls.company_b.id}
        )
        cls.location_output_company_b = cls.env["stock.location"].create(
            {"name": "Output - b", "usage": "internal", "company_id": cls.company_b.id}
        )
        cls.warehouse_company_b = cls.env["stock.warehouse"].create(
            {
                "name": "purchase warehouse - b",
                "code": "CMPb",
                "wh_input_stock_loc_id": cls.location_stock_company_b.id,
                "lot_stock_id": cls.location_stock_company_b.id,
                "wh_output_stock_loc_id": cls.location_output_company_b.id,
                "partner_id": cls.partner_company_b.id,
                "company_id": cls.company_b.id,
            }
        )
        cls.company_a.warehouse_id = cls.warehouse_company_a
        cls.company_a.sale_auto_validation = 1
        cls.company_b.warehouse_id = cls.warehouse_company_b
        cls.company_b.sale_auto_validation = 1

        cls.user_company_a.group_ids = [
            (
                6,
                0,
                [
                    cls.env.ref("account.group_account_manager"),
                    cls.env.ref("base.group_partner_manager"),
                    cls.env.ref("sales_team.group_sale_manager"),
                    cls.env.ref("purchase.group_purchase_user"),
                ],
            )
        ]
        cls.user_company_b.group_ids = [
            (
                6,
                0,
                [
                    cls.env.ref("account.group_account_manager"),
                    cls.env.ref("base.group_partner_manager"),
                    cls.env.ref("sales_team.group_sale_manager"),
                    cls.env.ref("purchase.group_purchase_user"),
                ],
            )
        ]

        cls.purchase_company_a = Form(cls.env["purchase.order"])
        cls.purchase_company_a.company_id = cls.company_a
        cls.purchase_company_a.partner_id = cls.partner_company_b

        with cls.purchase_company_a.order_line.new() as line_form:
            line_form.product_id = cls.product_consultant_multi_company
            line_form.product_qty = 3.0
            line_form.name = "Service Multi Company"
            line_form.price_unit = 450.0
        cls.purchase_company_a = cls.purchase_company_a.save()

        cls.sequence_purchase_journal_company_a = cls.env["ir.sequence"].create(
            {
                "name": "Account Expenses Journal Company A",
                "padding": 3,
                "prefix": "EXJ-A/%(year)s/",
                "company_id": cls.company_a.id,
            }
        )
        cls.sales_journal_company_b = cls.env["account.journal"].create(
            {
                "name": "Sales Journal - (Company B)",
                "code": "SAJ-B",
                "type": "sale",
                "sequence_id": cls.sequence_sale_journal_company_b.id,
                "default_credit_account_id": cls.a_sale_company_b.id,
                "default_debit_account_id": cls.a_sale_company_b.id,
                "company_id": cls.company_b.id,
            }
        )
        cls.purchases_journal_company_a = cls.env["account.journal"].create(
            {
                "name": "Purchases Journal - (Company A)",
                "code": "PAJ-A",
                "type": "purchase",
                "sequence_id": cls.sequence_purchase_journal_company_a.id,
                "default_credit_account_id": cls.a_expense_company_a.id,
                "default_debit_account_id": cls.a_expense_company_a.id,
                "company_id": cls.company_a.id,
            }
        )

        cls.company_b.so_from_po = True
        cls.purchase_manager_gr = cls.env.ref("purchase.group_purchase_manager")
        cls.sale_manager_gr = cls.env.ref("sales_team.group_sale_manager")
        cls.user_company_b = cls.user_company_b
        cls.purchase_manager_gr.users = [
            (4, cls.user_company_a.id, 4, cls.user_company_b.id)
        ]
        cls.sale_manager_gr.users = [
            (4, cls.user_company_a.id, 4, cls.user_company_b.id)
        ]
        cls.intercompany_sale_user_id = cls.user_company_b.copy()
        cls.intercompany_sale_user_id.company_ids |= cls.company_a
        cls.company_b.intercompany_sale_user_id = cls.intercompany_sale_user_id
        cls.account_sale_b = cls.a_sale_company_b
        cls.product_consultant = cls.product_consultant_multi_company
        # if product_multi_company is installed
        if "company_ids" in cls.env["product.template"]._fields:
            # We have to do that because the default method added a company
            cls.product_consultant.company_ids = False
        cls.product_consultant.with_user(
            cls.user_company_b.id
        ).property_account_income_id = cls.account_sale_b
        currency_eur = cls.env.ref("base.EUR")
        cls.purchase_company_a.currency_id = currency_eur
        pricelists = (
            cls.env["product.pricelist"]
            .sudo()
            .search([("currency_id", "!=", currency_eur.id)])
        )
        # set all price list to EUR
        for pl in pricelists:
            pl.currency_id = currency_eur

    def test_purchase_sale_inter_company(self):
        self.purchase_company_a.notes = "Test note"
        # Confirm the purchase of company A
        self.purchase_company_a.with_user(self.user_company_a).button_approve()
        # Check sale order created in company B
        sales = (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", self.purchase_company_a.id)])
        )
        self.assertNotEquals(sales, False)
        self.assertEquals(len(sales), 1)
        if sales.company_id.sale_auto_validation:
            self.assertEquals(sales.state, "sale")
        else:
            self.assertEquals(sales.state, "draft")
        self.assertEquals(
            sales.partner_id, self.purchase_company_a.company_id.partner_id
        )
        self.assertEquals(
            sales.company_id.partner_id, self.purchase_company_a.partner_id
        )
        self.assertEquals(
            len(sales.order_line), len(self.purchase_company_a.order_line)
        )
        self.assertEquals(
            sales.order_line.product_id, self.purchase_company_a.order_line.product_id,
        )
        self.assertEquals(sales.note, "Test note")

    def xxtest_date_planned(self):
        # Install sale_order_dates module
        module = self.env["ir.module.module"].search(
            [("name", "=", "sale_order_dates")]
        )
        if not module:
            return False
        module.button_install()
        self.purchase_company_a.date_planned = "2070-12-31"
        self.purchase_company_a.with_user(self.user_company_a).button_approve()
        sales = (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", self.purchase_company_a.id)])
        )
        self.assertEquals(sales.requested_date, "2070-12-31")

    def test_raise_product_access(self):
        product_rule = self.env.ref("product.product_comp_rule")
        product_rule.active = True
        # if product_multi_company is installed
        if "company_ids" in self.env["product.template"]._fields:
            self.product_consultant.company_ids = [(6, 0, [self.company_a.id])]
        self.product_consultant.company_id = self.company_a
        with self.assertRaises(UserError):
            self.purchase_company_a.with_user(self.user_company_a).button_approve()

    def test_raise_currency(self):
        currency = self.env.ref("base.USD")
        self.purchase_company_a.currency_id = currency
        with self.assertRaises(UserError):
            self.purchase_company_a.with_user(self.user_company_a).button_approve()

    def test_purchase_invoice_relation(self):
        self.purchase_company_a.with_user(self.user_company_a).button_approve()
        sales = (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", self.purchase_company_a.id)])
        )
        sale_invoice_id = sales._create_invoices()[0]
        sale_invoice_id.action_post()
        self.assertEquals(
            sale_invoice_id.auto_invoice_id, self.purchase_company_a.invoice_ids,
        )
        self.assertEquals(
            sale_invoice_id.auto_invoice_id.invoice_line_ids,
            self.purchase_company_a.order_line.invoice_lines,
        )

    def test_cancel(self):
        self.company_b.sale_auto_validation = False
        self.purchase_company_a.with_user(self.user_company_a).button_approve()
        sales = (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", self.purchase_company_a.id)])
        )
        self.assertEquals(self.purchase_company_a.partner_ref, sales.name)
        self.purchase_company_a.with_user(self.user_company_a).button_cancel()
        self.assertFalse(self.purchase_company_a.partner_ref)

    def test_cancel_confirmed_po_so(self):
        self.company_b.sale_auto_validation = True
        self.purchase_company_a.with_user(self.user_company_a).button_approve()
        self.env["sale.order"].with_user(self.user_company_b).search(
            [("auto_purchase_order_id", "=", self.purchase_company_a.id)]
        )
        with self.assertRaises(UserError):
            self.purchase_company_a.with_user(self.user_company_a).button_cancel()
