# Copyright 2015-2017 Chafique Delli <chafique.delli@akretion.com>
# Copyright 2020 Tecnativa - David Vidal
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.tests.common import SavepointCase
from odoo.exceptions import ValidationError, UserError
from odoo.modules.module import get_resource_path
from odoo.tools import convert_file


class TestAccountInvoiceInterCompanyBase(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        module = "account_invoice_inter_company"
        convert_file(
            cls.cr, module,
            get_resource_path(module, "tests", "inter_company_invoice.xml"),
            None, 'init', False, 'test', cls.registry._assertion_report,
        )
        cls.module = __name__.split('addons.')[1].split('.')[0]
        cls.account_obj = cls.env['account.account']
        cls.invoice_obj = cls.env['account.invoice']
        cls.company_a = cls.env.ref(cls.module + ".company_a")
        cls.invoice_company_a = cls.env.ref(
            cls.module + '.customer_invoice_company_a')
        cls.user_company_a = cls.env.ref(cls.module + '.user_company_a')
        cls.user_company_b = cls.env.ref(cls.module + '.user_company_b')
        cls.user_child_company_b = cls.env.ref(cls.module + '.child_partner_company_b')
        cls.invoice_line_a = cls.invoice_company_a.invoice_line_ids[0]
        cls.product_a = cls.invoice_line_a.product_id
        cls.invoice_line_b = cls.env["account.invoice.line"].create({
            "invoice_id": cls.invoice_company_a.id,
            "product_id": cls.product_a.id,
            "name": "Test second line",
            "account_id": cls.env.ref(cls.module + ".a_sale_company_a").id,
            "price_unit": 20,
        })
        cls.chart = cls.env['account.chart.template'].search([], limit=1)
        if not cls.chart:
            raise ValidationError(
                # translation to avoid pylint warnings
                _("No Chart of Account Template has been defined !"))


class TestAccountInvoiceInterCompany(TestAccountInvoiceInterCompanyBase):
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
        # ensure the catalog is shared
        self.env.ref('product.product_comp_rule').write({'active': False})
        # Make sure there are no taxes in target company for the used product
        self.product_a.with_context(
            force_company=self.user_company_b.id
        ).supplier_taxes_id = False
        # Put some analytic data for checking its propagation
        analytic_account = self.env['account.analytic.account'].create({
            'name': 'Test analytic account',
            'company_id': False,
        })
        analytic_tag = self.env['account.analytic.tag'].create({
            'name': 'Test analytic tag',
            'company_id': False,
        })
        self.invoice_line_a.account_analytic_id = analytic_account.id
        self.invoice_line_a.analytic_tag_ids = [(4, analytic_tag.id)]
        # Give user A permission to analytic
        self.user_company_a.groups_id = [
            (4, self.env.ref('analytic.group_analytic_accounting').id)]
        # Confirm the invoice of company A
        self.invoice_company_a.with_context(
            test_account_invoice_inter_company=True,
        ).sudo(self.user_company_a.id).action_invoice_open()
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
        invoice_line = invoices[0].invoice_line_ids[0]
        self.assertEquals(
            invoice_line.product_id, self.invoice_line_a.product_id)
        self.assertEquals(
            invoice_line.account_analytic_id,
            self.invoice_line_a.account_analytic_id)
        self.assertEquals(
            invoice_line.analytic_tag_ids,
            self.invoice_line_a.analytic_tag_ids)

    def test04_cancel_invoice(self):
        # Confirm the invoice of company A
        self.invoice_company_a.with_context(
            test_account_invoice_inter_company=True,
        ).sudo(self.user_company_a.id).action_invoice_open()
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

    def test_confirm_invoice_with_child_partner(self):
        # ensure the catalog is shared
        self.env.ref('product.product_comp_rule').write({'active': False})
        # When a contact of the company is defined as partner,
        # it also must trigger the intercompany workflow
        self.invoice_company_a.write({"partner_id": self.user_child_company_b.id})
        # Confirm the invoice of company A
        self.invoice_company_a.with_context(
            test_account_invoice_inter_company=True,
        ).sudo(self.user_company_a.id).action_invoice_open()
        # Check destination invoice created in company B
        invoices = self.invoice_obj.sudo(self.user_company_b.id).search([
            ('auto_invoice_id', '=', self.invoice_company_a.id)
        ])
        self.assertEqual(len(invoices), 1)

    def test_confirm_invoice_with_product_and_shared_catalog(self):
        """ With no security rule, child company have access to any product.
            Then child invoice can share the same product
        """
        # ensure the catalog is shared even if product is in other company
        self.env.ref('product.product_comp_rule').write({'active': False})
        # Product is set to a specific company
        self.product_a.write({"company_id": self.company_a.id})
        invoices = self._confirm_invoice_with_product()
        self.assertNotEqual(
            invoices.invoice_line_ids[0].product_id, self.env["product.product"])

    def test_confirm_invoice_with_native_product_rule_and_shared_product(self):
        """ With native security rule, products with access in both companies
            must be present in parent and child invoices.
        """
        # ensure the catalog is shared even if product is in other company
        self.env.ref('product.product_comp_rule').write({'active': True})
        # Product is set to a specific company
        self.product_a.write({"company_id": False})
        invoices = self._confirm_invoice_with_product()
        self.assertEqual(
            invoices.invoice_line_ids[0].product_id, self.product_a)

    def test_confirm_invoice_with_native_product_rule_and_unshared_product(self):
        """ With native security rule, products with no access in both companies
            must prevent child invoice creation.
        """
        # ensure the catalog is shared even if product is in other company
        self.env.ref('product.product_comp_rule').write({'active': True})
        # Product is set to a specific company
        self.product_a.write({"company_id": self.company_a.id})
        with self.assertRaises(UserError):
            self._confirm_invoice_with_product()

    def _confirm_invoice_with_product(self):
        # Confirm the invoice of company A
        self.invoice_company_a.with_context(
            test_account_invoice_inter_company=True,
        ).sudo(self.user_company_a.id).action_invoice_open()
        # Check destination invoice created in company B
        invoices = self.invoice_obj.sudo(self.user_company_b.id).search([
            ('auto_invoice_id', '=', self.invoice_company_a.id)
        ])
        self.assertEqual(len(invoices), 1)
        return invoices
