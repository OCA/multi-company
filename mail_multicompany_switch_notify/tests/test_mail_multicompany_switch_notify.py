# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, new_test_user


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
        cls.env.user.company_ids |= cls.company

    def test_company_has_mail_server(self):
        """A company with an explicitly assigned server returns True."""
        self.assertTrue(self.company.has_outgoing_mail_server())

    def test_company_without_mail_server(self):
        """A company with no assigned server returns False."""
        company_no_server = self.env["res.company"].create(
            {"name": "No Server Company"}
        )
        self.env.user.company_ids |= company_no_server
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
        self.env.user.company_ids |= company_no_own_server
        self.assertFalse(company_no_own_server.has_outgoing_mail_server())

    def test_other_company_access_denied(self):
        """A user cannot check a company they do not belong to."""
        user = new_test_user(
            self.env,
            login="switch_notify_user",
            groups="base.group_user",
            company_id=self.env.ref("base.main_company").id,
            company_ids=[(6, 0, self.env.ref("base.main_company").ids)],
        )
        with self.assertRaises(AccessError):
            self.company.with_user(user).has_outgoing_mail_server()
