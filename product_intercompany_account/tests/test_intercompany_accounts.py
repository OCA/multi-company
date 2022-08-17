from odoo.tests.common import TransactionCase


class TestIntercompanyAccounts(TransactionCase):
    def setUp(self):
        super(TestIntercompanyAccounts, self).setUp()
        self.company_a = self.env["res.company"].create({"name": "Company A"})
        self.company_b = self.env["res.company"].create({"name": "company b"})

        self.partner = self.env["res.partner"].create({"name": "Partner"})

        self.income_account_type_a = self.env["account.account.type"].create(
            {"name": "Income type A", "internal_group": "income"}
        )
        self.income_account_a = self.env["account.account"].create(
            {
                "name": "Income A",
                "code": "Income A",
                "user_type_id": self.income_account_type_a.id,
                "company_id": self.company_a.id,
                "reconcile": True,
            }
        )
        self.income_inter_account_type_a = self.env["account.account.type"].create(
            {"name": "Income Inter type A", "internal_group": "income"}
        )
        self.income_inter_account_a = self.env["account.account"].create(
            {
                "name": "Income Inter A",
                "code": "Income Inter A",
                "user_type_id": self.income_account_type_a.id,
                "company_id": self.company_a.id,
                "reconcile": True,
            }
        )

        self.product_consultant = self.env["product.product"].create(
            {
                "name": "Product service",
                "uom_id": self.env.ref("uom.product_uom_hour").id,
                "uom_po_id": self.env.ref("uom.product_uom_hour").id,
                "categ_id": self.env.ref("product.product_category_all").id,
                "type": "service",
                "company_id": False,
                "invoice_policy": "order",
                "property_account_income_id": self.income_account_a.id,
                "property_account_income_intercompany": self.income_inter_account_a.id,
            }
        )

        self.sale_order_1 = self.env["sale.order"].create(
            {"partner_id": self.company_b.partner_id.id}
        )
        self.order_line_1 = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order_1.id,
                "product_id": self.product_consultant.id,
                "product_uom": self.product_consultant.uom_id.id,
                "product_uom_qty": 10.0,
                "price_unit": 100.0,
            }
        )
        self.sale_order_2 = self.env["sale.order"].create(
            {"partner_id": self.partner.id}
        )
        self.order_line_1 = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order_2.id,
                "product_id": self.product_consultant.id,
                "product_uom": self.product_consultant.uom_id.id,
                "product_uom_qty": 10.0,
                "price_unit": 100.0,
            }
        )

    def test_intercompany_order(self):
        self.sale_order_1.action_confirm()
        invoice_id = self.sale_order_1.action_invoice_create()
        invoices = self.env["account.invoice"].browse(invoice_id)
        self.assertEquals(
            invoices.invoice_line_ids.account_id.id,
            self.product_consultant.property_account_income_intercompany.id,
        )

    def test_normal_so(self):
        self.sale_order_2.action_confirm()
        invoice_id_2 = self.sale_order_2.action_invoice_create()
        invoices_2 = self.env["account.invoice"].browse(invoice_id_2)
        self.assertEquals(
            invoices_2.invoice_line_ids.account_id.id,
            self.product_consultant.property_account_income_id.id,
        )
