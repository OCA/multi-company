from odoo.tests.common import TransactionCase


class TestIntercompanyAccounts(TransactionCase):
    def setUp(cls):
        super(TestIntercompanyAccounts, cls).setUp()

        cls.company_a = cls.env['res.company'].create({
            'name': 'Company A',
        })
        cls.company_b = cls.env['res.company'].create({
            'name': 'Company B',
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

        cls.product_consultant = cls.env['product.product'].with_context(force_company=cls.company_a.id).create({
            'name': 'Product service',
            'uom_id': cls.env.ref('uom.product_uom_hour').id,
            'uom_po_id': cls.env.ref('uom.product_uom_hour').id,
            'categ_id': cls.env.ref('product.product_category_all').id,
            'type': 'product',
            'company_id': cls.company_a.id,
            'invoice_policy': 'delivery',
            'property_account_income_id': cls.income_account_a.id,
            'property_account_income_intercompany': cls.income_inter_account_a.id,
        })

        cls.sale_order_1 = cls.env["sale.order"].create(
            {"partner_id": cls.company_b.partner_id.id,
             "company_id": cls.company_a.id}
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
            {"partner_id": cls.partner.id,
             "company_id": cls.company_a.id}
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

        cls.journal_sale = cls.env['account.journal'].create({
            'name': 'Sale Journal - Test',
            'code': 'AJ-SALE',
            'type': 'sale',
            'company_id': cls.company_a.id,
            'default_debit_account_id': cls.income_account_a.id,
            'default_credit_account_id': cls.income_account_a.id,
        })

        cls.context = {
            'active_model': 'sale.order',
            'active_ids': [cls.sale_order_1.id],
            'active_id': cls.sale_order_1.id,
            'default_journal_id': cls.journal_sale.id,
        }

    def test_intercompany_order(self):
        self.sale_order_1.action_confirm()
        self.sale_order_1.picking_ids[0].move_ids_without_package[0].quantity_done = 10.0
        self.sale_order_1.picking_ids[0].button_validate()
        print(self.sale_order_1.picking_ids[0].state)
        payment = self.env['sale.advance.payment.inv'].with_context(self.context).create({
            'advance_payment_method': 'delivered'
         })
        #self.sale_order_1._create_invoices()
        payment.with_context(open_invoices=True).create_invoices()
        move_1 = self.sale_order_1.invoice_ids[0]
        move_1.action_post()

        self.assertEquals(
            self.sale_order_1.invoice_ids[0].invoice_line_ids.account_id.id,
            self.product_consultant.property_account_income_intercompany.id,
        )

    #def test_normal_so(self):
     #   self.sale_order_2.action_confirm()
        #payment = self.env['sale.advance.payment.inv'].with_context(self.context).create({
        #    'advance_payment_method': 'delivered'
        #})
        #payment.create_invoices()
    #    self.sale_order_2._create_invoices()
        #move_2 = self.sale_order.invoice_ids[0]
        #move_2.post()

        #moves_2 = self.sale_order_2.with_context(force_company=self.company_a.id)._create_invoices()
     #   self.assertEquals(
     #       moves_2.invoice_line_ids.account_id.id,
     #       self.product_consultant.property_account_income_id.id,
     #   )
