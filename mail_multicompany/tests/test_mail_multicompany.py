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
        # Server on message should be empty as the copany on user is still
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
