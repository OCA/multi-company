# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestMailMulticompanySwitchNotify(TransactionCase):
    """Test the has_outgoing_mail_server() method added by this module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({"name": "Test Company"})
        cls.server = cls.env["ir.mail_server"].create(
            {
                "name": "Test Server",
                "smtp_host": "test.smtp.example.com",
                "company_id": cls.company.id,
            }
        )

    def test_company_has_mail_server(self):
        """A company with an explicitly assigned server returns True."""
        self.assertTrue(self.company.has_outgoing_mail_server())

    def test_company_without_mail_server(self):
        """A company with no assigned server returns False."""
        company_no_server = self.env["res.company"].create(
            {"name": "No Server Company"}
        )
        self.assertFalse(company_no_server.has_outgoing_mail_server())

    def test_global_server_not_counted(self):
        """A global server (company_id=False) is NOT counted for any company."""
        self.env["ir.mail_server"].create(
            {
                "name": "Global Server",
                "smtp_host": "global.smtp.example.com",
                "company_id": False,
            }
        )
        company_no_own_server = self.env["res.company"].create(
            {"name": "Another Company"}
        )
        self.assertFalse(company_no_own_server.has_outgoing_mail_server())
