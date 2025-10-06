from lxml import etree

from odoo.tests import TransactionCase, tagged
from odoo.tools.safe_eval import safe_eval


@tagged("post_install", "-at_install")
class TestResCompanySearchView(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Company = cls.env["res.company"]
        cls.company_alpha = cls.Company.create(
            {
                "name": "Alpha Logistics",
                "vat": "BE123456789",
                "email": "info@alpha.com",
                "phone": "0123456789",
            }
        )
        cls.company_beta = cls.Company.create(
            {
                "name": "Beta Transport",
                "vat": "BE987654321",
                "email": "contact@beta.com",
                "phone": "0470123456",
            }
        )

        # Load your search view
        cls.view = cls.env.ref("res_company_search_view.view_res_company_search")

    def _get_field_domain(self, field_name, search_value):
        """Helper: evaluate filter_domain for a <field> node."""
        arch = etree.fromstring(self.view.arch_db)
        node = arch.xpath(f"//field[@name='{field_name}']")
        if not node:
            self.fail(f"No <field name='{field_name}'> found in search view.")
        filter_domain = node[0].get("filter_domain")
        return safe_eval(filter_domain, {"self": search_value})

    def _get_filter_domain(self, filter_name):
        """Helper: evaluate domain for a <filter> node."""
        arch = etree.fromstring(self.view.arch_db)
        node = arch.xpath(f"//filter[@name='{filter_name}']")
        if not node:
            self.fail(f"No <filter name='{filter_name}'> found in search view.")
        domain = node[0].get("domain")
        return safe_eval(domain or "[]")

    # ---------- Tests ----------

    def test_name_filter_domain(self):
        """Search by name/vat/company_registry."""
        domain = self._get_field_domain("name", "Beta")
        result = self.Company.search(domain)
        self.assertIn(self.company_beta, result)
        self.assertNotIn(self.company_alpha, result)

    def test_email_filter_domain(self):
        """Search by email."""
        domain = self._get_field_domain("email", "alpha.com")
        result = self.Company.search(domain)
        self.assertIn(self.company_alpha, result)
        self.assertNotIn(self.company_beta, result)

    def test_phone_filter_domain(self):
        """Search by phone or mobile."""
        domain = self._get_field_domain("phone", "0470")
        result = self.Company.search(domain)
        self.assertIn(self.company_beta, result)
        self.assertNotIn(self.company_alpha, result)

    def test_archived_filter(self):
        """Ensure Archived filter domain works."""
        self.company_beta.active = False
        domain = self._get_filter_domain("inactive")
        result = self.Company.search(domain)
        self.assertIn(self.company_beta, result)
        self.assertNotIn(self.company_alpha, result)
