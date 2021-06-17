from odoo.tests.common import TransactionCase


class TestIntercompanyAccounts(TransactionCase):

    def setUp(cls):
        super(TestIntercompanyAccounts, cls).setUp()
        cls.company_a = cls.env['res.company'].create({
            'name': 'Company A',
        })
        cls.company_b = cls.env['res.company'].create({
            'name': 'company b',
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Partner'
        })

        cls.income_account_type_a = cls.env['account.account.type'].create({
            "name": "Income type A",
            "internal_group": "income",
        })
        cls.income_account_a = cls.env['account.account'].create({
            "name": "Income A",
            "code": "Income A",
            "user_type_id": cls.income_account_type_a.id,
            "company_id": cls.company_a.id,
            "reconcile": True,
        })
        cls.income_inter_account_type_a = cls.env['account.account.type'].create({
            "name": "Income Inter type A",
            "internal_group": "income",
        })
        cls.income_inter_account_a = cls.env['account.account'].create({
            "name": "Income Inter A",
            "code": "Income Inter A",
            "user_type_id": cls.income_account_type_a.id,
            "company_id": cls.company_a.id,
            "reconcile": True,
        })

        cls.product_consultant = cls.env['product.product'].create({
            'name': 'Product service',
            'uom_id': cls.env.ref('uom.product_uom_hour').id,
            'uom_po_id': cls.env.ref('uom.product_uom_hour').id,
            'categ_id': cls.env.ref('product.product_category_all').id,
            'type': 'service',
            'company_id': False,
            'invoice_policy': 'order',
            'property_account_income_id': cls.income_account_a.id,
            'property_account_income_intercompany': cls.income_inter_account_a.id,
        })

        cls.sale_order_1 = cls.env["sale.order"].create(
            {"partner_id": cls.company_b.partner_id.id}
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
            {"partner_id": cls.partner.id}
        )
        cls.order_line_1 = cls.env["sale.order.line"].create(
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
        invoice_id = self.sale_order_1.action_invoice_create()
        invoices = self.env['account.invoice'].browse(invoice_id)
        self.assertEquals(
            invoices.invoice_line_ids.account_id.id,
            self.product_consultant.property_account_income_intercompany.id,
        )

    def test_normal_so(self):
        self.sale_order_2.action_confirm()
        invoice_id_2 = self.sale_order_2.action_invoice_create()
        invoices_2 = self.env['account.invoice'].browse(invoice_id_2)
        self.assertEquals(
            invoices_2.invoice_line_ids.account_id.id,
            self.product_consultant.property_account_income_id.id,
        )
