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
    def _create_warehouse(cls, code, company, use_company_address=True):
        if use_company_address:
            address = company.partner_id
        else:
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
    def _create_purchase_order(cls):
        po = Form(cls.env["purchase.order"])
        po.company_id = cls.company_a
        po.partner_id = cls.partner_company_b

        cls.product.invoice_policy = "order"

        with po.order_line.new() as line_form:
            line_form.product_id = cls.product
            line_form.product_qty = 3.0
            line_form.name = "Service Multi Company"
            line_form.price_unit = 450.0
        return po.save()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.product_consultant_multi_company

        if "company_ids" in cls.env["res.partner"]._fields:
            # We have to do that because the default method added a company
            cls.partner_company_a.company_ids = [(6, 0, cls.company_a.ids)]
            cls.partner_company_b.company_ids = [(6, 0, cls.company_b.ids)]

        # Configure 2 Warehouse per company
        cls.warehouse_a = cls._create_warehouse("CA-WA", cls.company_a)
        cls.warehouse_b = cls._create_warehouse(
            "CA-WB", cls.company_a, use_company_address=False
        )

        cls.warehouse_c = cls._create_warehouse("CB-WC", cls.company_b)
        cls.warehouse_d = cls._create_warehouse(
            "CB-WD", cls.company_b, use_company_address=False
        )

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
        cls.purchase_company_a = cls._create_purchase_order()

        # Configure pricelist to USD
        cls.env["product.pricelist"].sudo().search([]).write(
            {"currency_id": cls.env.ref("base.USD").id}
        )

    def _approve_po(self):
        self.purchase_company_a.with_user(self.user_company_a).button_approve()

    def _get_sale(self):
        return (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", self.purchase_company_a.id)])
        )

    def test_purchase_sale_inter_company(self):
        self.purchase_company_a.notes = "Test note"
        # Confirm the purchase of company A
        self._approve_po()
        # Check sale order created in company B
        sale = self._get_sale()
        self.assertEqual(len(sale), 1)
        self.assertEqual(sale.state, "sale")
        self.assertEqual(sale.partner_id, self.purchase_company_a.company_id.partner_id)
        self.assertEqual(sale.company_id.partner_id, self.purchase_company_a.partner_id)
        self.assertEqual(len(sale.order_line), len(self.purchase_company_a.order_line))
        self.assertEqual(
            sale.order_line.product_id,
            self.purchase_company_a.order_line.product_id,
        )
        self.assertEqual(sale.note, "Test note")

    def test_not_auto_validate(self):
        self.company_b.sale_auto_validation = False
        self._approve_po()
        sale = self._get_sale()
        self.assertEqual(sale.state, "draft")

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
        self.assertEqual(sales.requested_date, "2070-12-31")

    def test_raise_product_access(self):
        product_rule = self.env.ref("product.product_comp_rule")
        product_rule.active = True
        # if product_multi_company is installed
        if "company_ids" in self.env["product.template"]._fields:
            self.product.company_ids = [(6, 0, [self.company_a.id])]
        self.product.company_id = self.company_a
        with self.assertRaises(UserError):
            self.purchase_company_a.with_user(self.user_company_a).button_approve()

    def test_raise_currency(self):
        currency = self.env.ref("base.EUR")
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
        self.assertEqual(
            sale_invoice_id.auto_invoice_id,
            self.purchase_company_a.invoice_ids,
        )
        self.assertEqual(
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
        self.assertEqual(self.purchase_company_a.partner_ref, sales.name)
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
