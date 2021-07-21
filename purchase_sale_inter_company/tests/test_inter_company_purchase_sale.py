# Copyright 2013-Today Odoo SA
# Copyright 2019-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import common
from odoo.exceptions import AccessError, UserError
from odoo.modules.module import get_resource_path
from odoo.tools import convert_file


class TestPurchaseSaleInterCompany(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._load(
            "account_invoice_inter_company",
            "tests",
            "inter_company_invoice.xml",
        )
        cls._load(
            "purchase_sale_inter_company",
            "tests",
            "inter_company_purchase_sale.xml",
        )
        cls.purchase_company_a = cls.env.ref(
            'purchase_sale_inter_company.purchase_company_a')
        cls.sale_company_b = cls.env.ref(
            'purchase_sale_inter_company.sale_company_b')
        cls.company_a = cls.env.ref('purchase_sale_inter_company.company_a')
        cls.company_b = cls.env.ref('purchase_sale_inter_company.company_b')
        cls.company_b.so_from_po = True
        cls.purchase_manager_gr = cls.env.ref(
            'purchase.group_purchase_manager')
        cls.sale_manager_gr = cls.env.ref('sales_team.group_sale_manager')
        cls.user_a = cls.env.ref('purchase_sale_inter_company.user_company_a')
        cls.user_b = cls.env.ref('purchase_sale_inter_company.user_company_b')
        cls.purchase_manager_gr.users = [
            (4, cls.user_a.id), (4, cls.user_b.id)]
        cls.sale_manager_gr.users = [(4, cls.user_a.id), (4, cls.user_b.id)]
        cls.intercompany_user = cls.user_b.copy()
        cls.intercompany_user.company_ids |= cls.company_a
        cls.company_b.intercompany_user_id = cls.intercompany_user
        cls.account_sale_b = cls.env.ref(
            'purchase_sale_inter_company.a_sale_company_b')
        cls.product_consultant = cls.env.ref(
            'purchase_sale_inter_company.product_consultant_multi_company')
        cls.product_consultant.sudo(
            cls.user_b.id).property_account_income_id = cls.account_sale_b
        currency_eur = cls.env.ref('base.EUR')
        cls.purchase_company_a.currency_id = currency_eur
        pricelists = cls.env['product.pricelist'].sudo().search([
            ('currency_id', '!=', currency_eur.id)
        ])
        cls.company_b.intercompany_overwrite_purchase_price = True
        cls.company_a.intercompany_overwrite_purchase_price = True
        # set all price list to EUR
        for pl in pricelists:
            pl.currency_id = currency_eur

    @classmethod
    def _load(cls, module, *args):
        convert_file(
            cls.cr, "purchase_sale_inter_company",
            get_resource_path(module, *args),
            {}, 'init', False, 'test', cls.registry._assertion_report,
        )

    def test_do_not_sync_prices_and_raise(self):
        """ If do_not_sync_prices is set to True assert prices for
        corresponding PO - SO lines are the same
        """
        self.company_b.sale_auto_validation = True
        self.company_a.intercompany_overwrite_purchase_price = False
        with self.assertRaises(UserError):
            self.purchase_company_a.sudo(self.user_a).button_approve()

    def test_purchase_sale_inter_company(self):
        self.purchase_company_a.notes = 'Test note'
        # Confirm the purchase of company A
        self.purchase_company_a.sudo(self.user_a).button_approve()
        # Check sale order created in company B
        sales = self.env['sale.order'].sudo(self.user_b).search([
            ('auto_purchase_order_id', '=', self.purchase_company_a.id)
        ])
        self.assertNotEquals(sales, False)
        self.assertEquals(len(sales), 1)
        if sales.company_id.sale_auto_validation:
            self.assertEquals(sales.state, 'sale')
        else:
            self.assertEquals(sales.state, 'draft')
        self.assertEquals(sales.partner_id,
                          self.purchase_company_a.company_id.partner_id)
        self.assertEquals(sales.company_id.partner_id,
                          self.purchase_company_a.partner_id)
        self.assertEquals(len(sales.order_line),
                          len(self.purchase_company_a.order_line))
        self.assertEquals(sales.order_line.product_id,
                          self.purchase_company_a.order_line.product_id)
        self.assertEquals(sales.note, 'Test note')

    def xxtest_date_planned(self):
        # Install sale_order_dates module
        module = self.env['ir.module.module'].search(
            [('name', '=', 'sale_order_dates')])
        if not module:
            return False
        module.button_install()
        self.purchase_company_a.date_planned = '2070-12-31'
        self.purchase_company_a.sudo(self.user_a).button_approve()
        sales = self.env['sale.order'].sudo(self.user_b).search([
            ('auto_purchase_order_id', '=', self.purchase_company_a.id),
        ])
        self.assertEquals(sales.requested_date, '2070-12-31')

    def test_raise_product_access(self):
        product_rule = self.env.ref('product.product_comp_rule')
        product_rule.active = True
        self.product_consultant.company_id = self.company_b
        with self.assertRaises(AccessError):
            self.purchase_company_a.sudo(self.user_a).button_approve()

    def test_raise_currency(self):
        currency = self.env.ref('base.USD')
        self.purchase_company_a.currency_id = currency
        with self.assertRaises(UserError):
            self.purchase_company_a.sudo(self.user_a).button_approve()

    def test_purchase_invoice_relation(self):
        self.purchase_company_a.sudo(self.user_a).button_approve()
        sales = self.env['sale.order'].sudo(self.user_b).search([
            ('auto_purchase_order_id', '=', self.purchase_company_a.id),
        ])
        sale_invoice_id = sales.action_invoice_create()[0]
        sale_invoice = self.env['account.invoice'].browse(sale_invoice_id)
        sale_invoice.action_invoice_open()
        self.assertEquals(sale_invoice.auto_invoice_id,
                          self.purchase_company_a.invoice_ids)
        self.assertEquals(sale_invoice.auto_invoice_id.invoice_line_ids,
                          self.purchase_company_a.order_line.invoice_lines)

    def test_cancel(self):
        self.company_b.sale_auto_validation = False
        self.purchase_company_a.sudo(self.user_a).button_approve()
        sales = self.env['sale.order'].sudo(self.user_b).search([
            ('auto_purchase_order_id', '=', self.purchase_company_a.id)
        ])
        self.assertEquals(self.purchase_company_a.partner_ref, sales.name)
        self.purchase_company_a.sudo(self.user_a).button_cancel()
        self.assertFalse(self.purchase_company_a.partner_ref)

    def test_cancel_confirmed_po_so(self):
        self.company_b.sale_auto_validation = True
        self.purchase_company_a.sudo(self.user_a).button_approve()
        self.env['sale.order'].sudo(self.user_b).search([
            ('auto_purchase_order_id', '=', self.purchase_company_a.id)
        ])
        with self.assertRaises(UserError):
            self.purchase_company_a.sudo(self.user_a).button_cancel()

    def test_sale_purchase_inter_company(self):
        self.company_b.so_from_po = False
        self.company_a.po_from_so = True
        warehouse_company_a = self.env.ref(
            'purchase_sale_inter_company.warehouse_company_a')
        self.company_a.po_picking_type_id = warehouse_company_a.in_type_id.id
        intercompany_user_a = self.user_a.copy()
        intercompany_user_a.company_ids |= self.company_b
        self.company_a.intercompany_user_id = intercompany_user_a
        self.sale_company_b.note = 'Test sale note'
        self.sale_company_b.sudo(self.user_b).action_confirm()
        purchases = self.env['purchase.order'].sudo(self.user_a).search([
            ('auto_sale_order_id', '=', self.sale_company_b.id)
        ])
        self.assertEquals(len(purchases), 1)
        if purchases.company_id.purchase_auto_validation:
            self.assertEquals(purchases.state, 'purchase')
        else:
            self.assertEquals(purchases.state, 'draft')
        self.assertEquals(purchases.partner_id,
                          self.sale_company_b.company_id.partner_id)
        self.assertEquals(purchases.company_id.partner_id,
                          self.sale_company_b.partner_id)
        self.assertEquals(len(purchases.order_line),
                          len(self.sale_company_b.order_line))
        self.assertEquals(purchases.order_line.product_id,
                          self.sale_company_b.order_line.product_id)
        self.assertEquals(purchases.order_line.product_qty,
                          self.sale_company_b.order_line.product_uom_qty)
        self.assertEquals(purchases.notes, 'Test sale note')
