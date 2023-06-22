# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestMailMultiCompany(TransactionCase):
    def _create_message(self):
        return (
            self.env["mail.message"]
            .sudo(self.user_demo)
            .create(
                {
                    "reply_to": "test.reply@example.com",
                    "email_from": "test.from@example.com",
                    "author_id": self.user_demo.partner_id.id,
                }
            )
        )

    def setUp(self):
        super().setUp()
        self.user_demo = self.env.ref("base.user_demo")
        company_obj = self.env["res.company"]
        server_obj = self.env["ir.mail_server"]
        self.company1 = company_obj.create({"name": "Company 1"})
        self.company2 = company_obj.create({"name": "Company 2"})
        self.user_demo.write(
            {
                "company_id": self.company1.id,
                "company_ids": [(4, self.company1.id), (4, self.company2.id)],
            }
        )
        self.server1 = server_obj.create(
            {"name": "server 1", "smtp_host": "test.smtp1", "sequence": 1}
        )
        self.server2 = server_obj.create(
            {"name": "server 2", "smtp_host": "test.smtp2", "sequence": 2})

    def test_mail_message_no_company_restriction(self):
        # no company_id set on server, so it's should be the first on list
        msg = self._create_message()
        self.assertEqual(msg.mail_server_id.id, self.server1.id)

    def test_mail_message_company_restriction(self):
        # set company 1 on server 1
        # server on message should be server 1
        self.server1.write({"company_id": self.company1.id})
        msg = self._create_message()
        self.assertEqual(msg.mail_server_id.id, self.server1.id)

        # Set company 2 on server 1 and server 2
        # Server on message should be empty as the company on user is still
        # Company 1
        self.server1.write({"company_id": self.company2.id})
        self.server2.write({"company_id": self.company2.id})
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
