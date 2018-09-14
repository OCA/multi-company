# Copyright 2015-2017 Chafique Delli <chafique.delli@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.tests.common import SavepointCase
from odoo.exceptions import ValidationError
from odoo.modules.module import get_resource_path
from odoo.tools import convert_file


class TestAccountInvoiceInterCompany(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestAccountInvoiceInterCompany, cls).setUpClass()
        module = "account_invoice_inter_company"
        convert_file(
            cls.cr, module,
            get_resource_path(module, "tests", "inter_company_invoice.xml"),
            None, 'init', False, 'test', cls.registry._assertion_report,
        )
        cls.wizard_obj = cls.env['wizard.multi.charts.accounts']
        cls.account_obj = cls.env['account.account']
        cls.invoice_obj = cls.env['account.invoice']
        cls.invoice_company_a = cls.env.ref(
            'account_invoice_inter_company.customer_invoice_company_a')
        cls.user_company_a = cls.env.ref(
            'account_invoice_inter_company.user_company_a')
        cls.user_company_b = cls.env.ref(
            'account_invoice_inter_company.user_company_b')

        cls.chart = cls.env['account.chart.template'].search([], limit=1)
        if not cls.chart:
            raise ValidationError(
                # translation to avoid pylint warnings
                _("No Chart of Account Template has been defined !"))

    def test01_user(self):
        # Check user of company B (company of destination)
        # with which we check the intercompany product
        self.assertNotEquals(self.user_company_b.id, 1)
        orig_invoice = self.invoice_company_a
        dest_company = orig_invoice._find_company_from_invoice_partner()
        self.assertEquals(self.user_company_b.company_id, dest_company)
        self.assertIn(
            self.user_company_b.id,
            self.env.ref('account.group_account_invoice').users.ids)

    def test02_product(self):
        # Check product is intercompany
        for line in self.invoice_company_a.invoice_line_ids:
            self.assertFalse(line.product_id.company_id)

    def test03_confirm_invoice(self):
        # Confirm the invoice of company A
        self.invoice_company_a.sudo(
            self.user_company_a.id).action_invoice_open()
        # Check destination invoice created in company B
        invoices = self.invoice_obj.sudo(self.user_company_b.id).search([
            ('auto_invoice_id', '=', self.invoice_company_a.id)
        ])
        self.assertNotEquals(invoices, False)
        self.assertEquals(len(invoices), 1)
        if invoices.company_id.invoice_auto_validation:
            self.assertEquals(invoices[0].state, 'open')
        else:
            self.assertEquals(invoices[0].state, 'draft')
        self.assertEquals(invoices[0].partner_id,
                          self.invoice_company_a.company_id.partner_id)
        self.assertEquals(invoices[0].company_id.partner_id,
                          self.invoice_company_a.partner_id)
        self.assertEquals(len(invoices[0].invoice_line_ids),
                          len(self.invoice_company_a.invoice_line_ids))
        self.assertEquals(
            invoices[0].invoice_line_ids[0].product_id,
            self.invoice_company_a.invoice_line_ids[0].product_id)

    def test04_cancel_invoice(self):
        # Confirm the invoice of company A
        self.invoice_company_a.sudo(
            self.user_company_a.id).action_invoice_open()
        # Check state of invoices before to cancel invoice of company A
        self.assertEquals(self.invoice_company_a.state, 'open')
        invoices = self.invoice_obj.sudo(self.user_company_b.id).search([
            ('auto_invoice_id', '=', self.invoice_company_a.id)
        ])
        self.assertNotEquals(invoices[0].state, 'cancel')
        # Cancel the invoice of company A
        origin = ('%s - Canceled Invoice: %s') % (
            self.invoice_company_a.company_id.name,
            self.invoice_company_a.number)
        self.invoice_company_a.sudo(
            self.user_company_a.id).action_invoice_cancel()
        # Check invoices after to cancel invoice of company A
        self.assertEquals(self.invoice_company_a.state, 'cancel')
        self.assertEquals(invoices[0].state, 'cancel')
        self.assertEquals(invoices[0].origin, origin)
