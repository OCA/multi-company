# Copyright 2021 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from uuid import uuid4

from odoo.tests import HttpCase, tagged
from odoo.tests.common import TransactionCase


class TestResCompanyCode(TransactionCase):
    def _create_company(self, name, code):
        return self.env["res.company"].create({"name": name, "code": code})

    def test_complete_name(self):
        company = self._create_company("aName", "aCode")
        self.assertEqual(company.display_name, "aCode - aName")


@tagged("post_install", "-at_install")
class TestLoginSession(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = cls.env.ref("base.user_admin")

    def _get_session_info(self):
        response = self.url_open(
            "/web/session/get_session_info",
            data=json.dumps(dict(jsonrpc="2.0", method="call", id=str(uuid4()))),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_check_session_info(self):
        # Login as admin
        self.authenticate(user="admin", password="admin")
        self.assertEqual(self.session.uid, self.admin_user.id)

        # Check comapny name should be use display name
        data = self._get_session_info()
        companies = data["result"]["user_companies"]["allowed_companies"]
        for company in self.admin_user.company_ids:
            company_info = companies.get(str(company.id))
            self.assertEqual(company_info["name"], company.display_name)
