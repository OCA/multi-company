# Copyright 2015-2017 Chafique Delli <chafique.delli@akretion.com>
# Copyright 2020 Tecnativa - David Vidal
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import ValidationError
from odoo.modules.module import get_resource_path
from odoo.tests.common import SavepointCase
from odoo.tools import convert_file


class TestAccountInvoiceInterCompanyBase(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.module = __name__.split("addons.")[1].split(".")[0]
        convert_file(
            cls.cr,
            cls.module,
            get_resource_path(cls.module, "tests", "inter_company_invoice.xml"),
            None,
            "init",
            False,
            "test",
            cls.registry._assertion_report,
        )
        cls.account_obj = cls.env["account.account"]
        cls.account_move_obj = cls.env["account.move"]
        # if product_multi_company is installed
        if "company_ids" in cls.env["product.template"]._fields:
            # We have to do that because the default method added a company
            cls.env.ref(
                cls.module + ".product_consultant_multi_company"
            ).company_ids = False
        cls.invoice_company_a = cls.env.ref(cls.module + ".customer_invoice_company_a")
        cls.user_company_a = cls.env.ref(cls.module + ".user_company_a")
        cls.user_company_b = cls.env.ref(cls.module + ".user_company_b")
        cls.child_partner_company_b = cls.env.ref(
            cls.module + ".child_partner_company_b"
        )
        cls.company_a = cls.env.ref("account_invoice_inter_company.company_a")
        cls.company_b = cls.env.ref("account_invoice_inter_company.company_b")
        cls.company_a.invoice_auto_validation = True
        cls.invoice_line_a = cls.invoice_company_a.invoice_line_ids[0]
        cls.product_a = cls.invoice_line_a.product_id
        cls.product_a.with_context(
            force_company=cls.company_b.id
        ).property_account_expense_id = cls.env.ref(
            "account_invoice_inter_company.a_expense_company_b"
        ).id
        cls.invoice_line_b = cls.env["account.move.line"].create(
            {
                "move_id": cls.invoice_company_a.id,
                "product_id": cls.product_a.id,
                "name": "Test second line",
                "account_id": cls.env.ref(cls.module + ".a_sale_company_a").id,
                "price_unit": 20,
            }
        )
        cls.chart = cls.env["account.chart.template"].search([], limit=1)
        if not cls.chart:
            raise ValidationError(
                # translation to avoid pylint warnings
                _("No Chart of Account Template has been defined !")
            )


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
            self.env.ref("account.group_account_invoice").users.ids,
        )

    def test02_product(self):
        # Check product is intercompany
        for line in self.invoice_company_a.invoice_line_ids:
            self.assertFalse(line.product_id.company_id)

    def test03_confirm_invoice_and_cancel(self):
        # ensure the catalog is shared
        self.env.ref("product.product_comp_rule").write({"active": False})
        # Make sure there are no taxes in target company for the used product
        self.product_a.with_context(
            force_company=self.user_company_b.id
        ).supplier_taxes_id = False
        # Put some analytic data for checking its propagation
        analytic_account = self.env["account.analytic.account"].create(
            {"name": "Test analytic account", "company_id": False}
        )
        analytic_tag = self.env["account.analytic.tag"].create(
            {"name": "Test analytic tag", "company_id": False}
        )
        self.invoice_line_a.analytic_account_id = analytic_account.id
        self.invoice_line_a.analytic_tag_ids = [(4, analytic_tag.id)]
        # Give user A permission to analytic
        self.user_company_a.groups_id = [
            (4, self.env.ref("analytic.group_analytic_accounting").id)
        ]
        # Confirm the invoice of company A
        self.invoice_company_a.with_user(self.user_company_a.id).action_post()
        # Check destination invoice created in company B
        invoices = self.account_move_obj.with_user(self.user_company_b.id).search(
            [("auto_invoice_id", "=", self.invoice_company_a.id)]
        )
        self.assertNotEquals(invoices, False)
        self.assertEquals(len(invoices), 1)
        self.assertEquals(invoices[0].state, "posted")
        self.assertEquals(
            invoices[0].partner_id, self.invoice_company_a.company_id.partner_id
        )
        self.assertEquals(
            invoices[0].company_id.partner_id, self.invoice_company_a.partner_id
        )
        self.assertEquals(
            len(invoices[0].invoice_line_ids),
            len(self.invoice_company_a.invoice_line_ids),
        )
        invoice_line = invoices[0].invoice_line_ids[0]
        self.assertEquals(
            invoice_line.product_id,
            self.invoice_company_a.invoice_line_ids[0].product_id,
        )
        self.assertEquals(
            invoice_line.analytic_account_id, self.invoice_line_a.analytic_account_id
        )
        self.assertEquals(
            invoice_line.analytic_tag_ids, self.invoice_line_a.analytic_tag_ids
        )
        # Cancel the invoice of company A
        invoice_origin = ("%s - Canceled Invoice: %s") % (
            self.invoice_company_a.company_id.name,
            self.invoice_company_a.name,
        )
        self.invoice_company_a.with_user(self.user_company_a.id).button_cancel()
        # Check invoices after to cancel invoice of company A
        self.assertEquals(self.invoice_company_a.state, "cancel")
        self.assertEquals(invoices[0].state, "cancel")
        self.assertEquals(invoices[0].invoice_origin, invoice_origin)
        # Check if keep the invoice number
        invoice_number = self.invoice_company_a.name
        self.invoice_company_a.with_user(self.user_company_a.id).action_post()
        self.assertEquals(self.invoice_company_a.name, invoice_number)

    def test_confirm_invoice_with_child_partner(self):
        # ensure the catalog is shared
        self.env.ref("product.product_comp_rule").write({"active": False})
        # When a contact of the company is defined as partner,
        # it also must trigger the intercompany workflow
        self.invoice_company_a.write({"partner_id": self.child_partner_company_b.id})
        # Confirm the invoice of company A
        self.invoice_company_a.with_user(self.user_company_a.id).action_post()
        # Check destination invoice created in company B
        invoices = self.account_move_obj.with_user(self.user_company_b.id).search(
            [("auto_invoice_id", "=", self.invoice_company_a.id)]
        )
        self.assertEqual(len(invoices), 1)
