# Copyright 2013-Today Odoo SA
# Copyright 2019-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2023 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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
    def _create_internal_location(cls, name, company):
        return cls.env["stock.location"].create(
            {"name": name, "usage": "internal", "company_id": company.id}
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
    def setUpClass(cls):
        super().setUpClass()

        # Create warehouses
        cls.warehouse_company_a = cls._create_warehouse("CMPa", cls.company_a)
        cls.warehouse_company_b = cls._create_warehouse("CMPb", cls.company_b)

        # Create internal locations
        cls.location_stock_company_a = cls._create_internal_location(
            "Stock - a", cls.company_a
        )
        cls.location_output_company_a = cls._create_internal_location(
            "Output - a", cls.company_a
        )
        cls.location_stock_company_b = cls._create_internal_location(
            "Stock - b", cls.company_b
        )
        cls.location_output_company_b = cls._create_internal_location(
            "Output - b", cls.company_b
        )

        if "company_ids" in cls.env["res.partner"]._fields:
            # We have to do that because the default method added a company
            cls.partner_company_a.company_ids = [(6, 0, cls.company_a.ids)]
            cls.partner_company_b.company_ids = [(6, 0, cls.company_b.ids)]

        cls.company_a.warehouse_id = cls.warehouse_company_a
        cls.company_a.sale_auto_validation = 1
        cls.company_b.warehouse_id = cls.warehouse_company_b
        cls.company_b.sale_auto_validation = 1

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
        # Configure User
        cls._configure_user(cls.user_company_a)
        cls._configure_user(cls.user_company_b)

        cls.account_sale_b = cls.a_sale_company_b
        cls.product_consultant = cls.product_consultant_multi_company
        # if product_multi_company is installed
        if "company_ids" in cls.env["product.template"]._fields:
            # We have to do that because the default method added a company
            cls.product_consultant.company_ids = False
        cls.product_consultant.with_user(
            cls.user_company_b.id
        ).property_account_income_id = cls.account_sale_b
        # Configure pricelist to USD
        cls.env["product.pricelist"].sudo().search([]).write(
            {"currency_id": cls.env.ref("base.USD").id}
        )

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
        # Confirm the purchase of company A
        sale = self._approve_po(self.purchase_company_a)
        self.assertNotEquals(sale, False)
        self.assertEquals(len(sale), 1)
        if sale.company_id.sale_auto_validation:
            self.assertEquals(sale.state, "sale")
        else:
            self.assertEquals(sale.state, "draft")
        self.assertEquals(
            sale.partner_id, self.purchase_company_a.company_id.partner_id
        )
        self.assertEquals(
            sale.company_id.partner_id, self.purchase_company_a.partner_id
        )
        self.assertEquals(len(sale.order_line), len(self.purchase_company_a.order_line))
        self.assertEquals(
            sale.order_line.product_id, self.purchase_company_a.order_line.product_id,
        )
        self.assertEquals(sale.note, "Test note")

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
        self.assertEquals(sale.requested_date, "2070-12-31")

    def test_raise_product_access(self):
        product_rule = self.env.ref("product.product_comp_rule")
        product_rule.active = True
        # if product_multi_company is installed
        if "company_ids" in self.env["product.template"]._fields:
            self.product_consultant.company_ids = [(6, 0, [self.company_a.id])]
        self.product_consultant.company_id = self.company_a
        with self.assertRaises(UserError):
            self._approve_po(self.purchase_company_a)

    def test_raise_currency(self):
        currency = self.env.ref("base.EUR")
        self.purchase_company_a.currency_id = currency
        with self.assertRaises(UserError):
            self._approve_po(self.purchase_company_a)

    def test_purchase_invoice_relation(self):
        sale = self._approve_po(self.purchase_company_a)
        sale_invoice = sale._create_invoices()[0]
        sale_invoice.action_post()
        self.assertEqual(len(self.purchase_company_a.invoice_ids), 1)
        self.assertEqual(
            self.purchase_company_a.invoice_ids.auto_invoice_id, sale_invoice,
        )
        self.assertEqual(len(self.purchase_company_a.order_line.invoice_lines), 1)
        self.assertEqual(self.purchase_company_a.order_line.qty_invoiced, 3)

    def test_cancel(self):
        self.company_b.sale_auto_validation = False
        sale = self._approve_po(self.purchase_company_a)
        self.assertEquals(self.purchase_company_a.partner_ref, sale.name)
        self.purchase_company_a.with_user(self.user_company_a).button_cancel()
        self.assertFalse(self.purchase_company_a.partner_ref)

    def test_cancel_confirmed_po_so(self):
        self.company_b.sale_auto_validation = True
        self._approve_po(self.purchase_company_a)
        with self.assertRaises(UserError):
            self.purchase_company_a.with_user(self.user_company_a).button_cancel()
