# Copyright 2021 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TestResCompanyCode(SavepointCase):
    def _create_company(self, name, code):
        return self.env["res.company"].create({"name": name, "code": code})

    def test_complete_name(self):
        company = self._create_company("aName", "aCode")
        self.assertEqual(company.complete_name, "aCode - aName")

    def test_search_res_company(self):
        company = self._create_company("aName", "aCode")
        search_result = self.env["res.company"].name_search(name="aCode")
        self.assertEqual(company.id, search_result[0][0])
