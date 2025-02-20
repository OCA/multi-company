from odoo.tests.common import TransactionCase


class TestIntercompanyAccounts(TransactionCase):
    def setUp(cls):
        super().setUp()

        cls.company_b = cls.env["res.company"].create(
            {
                "name": "Company B",
            }
        )

        cls.partner = cls.env["res.partner"].create({"name": "Partner"})

        cls.income_account_a = cls.env["account.account"].create(
            {
                "name": "Income A",
                "code": "IncomeA",
                "reconcile": True,
                "account_type": "income",
            }
        )

        cls.income_inter_account_a = cls.env["account.account"].create(
            {
                "name": "Income Inter A",
                "code": "IncomeInterA",
                "reconcile": True,
                "account_type": "income",
            }
        )
        service_product_dict_create = {
            "name": "Product service",
            "uom_id": cls.env.ref("uom.product_uom_hour").id,
            "uom_po_id": cls.env.ref("uom.product_uom_hour").id,
            "categ_id": cls.env.ref("product.product_category_all").id,
            "type": "service",
            "company_id": False,
            "invoice_policy": "order",
            "property_account_income_id": cls.income_account_a.id,
            "property_account_income_intercompany": cls.income_inter_account_a.id,
        }
        cls.product_consultant = (
            cls.env["product.product"]
            .with_context()
            .create(service_product_dict_create)
        )
        cls.sale_order_1 = cls.env["sale.order"].create(
            {
                "partner_id": cls.company_b.partner_id.id,
            }
        )
        cls.order_line_1 = cls.env["sale.order.line"].create(
            {
                "order_id": cls.sale_order_1.id,
                "product_id": cls.product_consultant.id,
                "product_uom": cls.product_consultant.uom_id.id,
                "product_uom_qty": 10.0,
                "price_unit": 100.0,
            }
        )
        cls.sale_order_2 = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
            }
        )
        cls.order_line_2 = cls.env["sale.order.line"].create(
            {
                "order_id": cls.sale_order_2.id,
                "product_id": cls.product_consultant.id,
                "product_uom": cls.product_consultant.uom_id.id,
                "product_uom_qty": 10.0,
                "price_unit": 100.0,
            }
        )

    def test_intercompany_order(self):
        self.sale_order_1.action_confirm()
        self.sale_order_1._create_invoices()
        invoice_id = self.sale_order_1.invoice_ids[0]
        invoices = invoice_id
        self.assertEqual(
            invoices.invoice_line_ids.account_id.id,
            self.product_consultant.property_account_income_intercompany.id,
        )

    def test_normal_so(self):
        self.sale_order_2.action_confirm()
        self.sale_order_2._create_invoices()
        invoices_2 = self.sale_order_2.invoice_ids
        self.assertEqual(
            invoices_2.invoice_line_ids.account_id.id,
            self.product_consultant.property_account_income_id.id,
        )
