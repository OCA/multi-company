# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.tests.common import TransactionCase


class TestMailMultiCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_demo = cls.env.ref("base.user_demo")
        company_obj = cls.env["res.company"]
        server_obj = cls.env["ir.mail_server"]
        cls.company1 = company_obj.create({"name": "Company 1"})
        cls.company2 = company_obj.create({"name": "Company 2"})
        cls.user_demo.write(
            {
                "company_id": cls.company1.id,
                "company_ids": [
                    Command.link(cls.company1.id),
                    Command.link(cls.company2.id),
                ],
            }
        )
        cls.server1 = server_obj.create({"name": "server 1", "smtp_host": "teset.smtp"})
        cls.server2 = server_obj.create({"name": "server 1", "smtp_host": "test.smtp"})
        cls.mail_thread = cls.env["mail.thread"]
        cls.fetchmail_server = cls.env["fetchmail.server"].create(
            {
                "name": "Test Server",
                "company_id": cls.company2.id,
            }
        )

    def _create_message(self):
        return (
            self.env["mail.message"]
            .with_user(self.user_demo)
            .create(
                {
                    "reply_to": "test.reply@example.com",
                    "email_from": "test.from@example.com",
                    "author_id": self.user_demo.partner_id.id,
                }
            )
        )

    def test_01_mail_message_no_company_restriction(self):
        # no company_id set on server, so no one should be set on message

        msg = self._create_message()
        self.assertFalse(msg.mail_server_id)

    def test_02_mail_message_company_restriction(self):
        # set company 1 on server 1
        # server on message should be server 1
        self.server1.write({"company_id": self.company1.id})
        msg = self._create_message()
        self.assertEqual(msg.mail_server_id.id, self.server1.id)

        # Set company 2 on server 1
        # Server on message should be empty as the company on user is still
        # Company 1
        self.server1.write({"company_id": self.company2.id})
        msg = self._create_message()
        self.assertFalse(msg.mail_server_id)

        # Set company 2 on user
        # Server on message should be server 1
        self.user_demo.write({"company_id": self.company2.id})
        msg = self._create_message()
        self.assertEqual(msg.mail_server_id.id, self.server1.id)

        # Set Company 1 on server 1
        # Set Company 2 on server 2
        # Server on message should be server 2
        self.server1.write({"company_id": self.company1.id})
        self.server2.write({"company_id": self.company2.id})
        msg = self._create_message()
        self.assertEqual(msg.mail_server_id.id, self.server2.id)

        # Set Company 1 on user
        # Server on message should be server 1
        self.user_demo.write({"company_id": self.company1.id})
        msg = self._create_message()
        self.assertEqual(msg.mail_server_id.id, self.server1.id)

        # Set Company 1 in both servers
        # Server on message should be server 1 as no from_filters are set
        # and it will be the first to appear on the search
        self.server2.write({"company_id": self.company1.id})
        msg = self._create_message()
        self.assertEqual(msg.mail_server_id.id, self.server1.id)
        self.assertEqual(msg.email_from, "test.from@example.com")

    def test_message_process(self):
        fetchmail_server = self.fetchmail_server
        self.server2.write({"company_id": self.company2.id})

        # Create a mail alias and a message that can be processed
        # to see that the company context is correctly set
        res_partner_model = self.env["ir.model"].search([("model", "=", "res.partner")])
        customer = self.env["res.partner"].create({"name": "Test Partner"})

        self.env["mail.alias"].create(
            {
                "alias_name": "test_alias",
                "alias_model_id": res_partner_model.id,
                "alias_parent_model_id": res_partner_model.id,
                "alias_parent_thread_id": customer.id,
            }
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "mail.catchall.domain", "my_domain.com"
        )
        model = "res.partner"
        message = """MIME-Version: 1.0
            Date: Thu, 27 Dec 2018 16:27:45 +0100
            Message-ID: <thisisanid1>
            Subject: test message on test partner
            From:  Test Partner <test_partner@someprovider.com>
            To: test_alias@my_domain.com
            Content-Type: multipart/alternative; boundary="000000000000a47519057e029630"

            --000000000000a47519057e029630
            Content-Type: text/plain; charset="UTF-8"


            --000000000000a47519057e029630
            Content-Type: text/html; charset="UTF-8"
            Content-Transfer-Encoding: quoted-printable

            <div>Message content</div>

            --000000000000a47519057e029630--
            """
        context = {"default_fetchmail_server_id": fetchmail_server.id}

        # Call the message_process method
        result_id = self.mail_thread.with_context(**context).message_process(
            model, message
        )
        result = self.env["res.partner"].browse(result_id)
        # Add your assertions here to validate the result
        self.assertEqual(result.message_ids[0].mail_server_id, self.server2)
