# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase


class TestUtmSource(TransactionCase):
    def test_unique_name_constraint(self):
        company = self.env["res.company"].create({"name": "test"})
        old = self.env.ref("utm.utm_source_search_engine")
        new = self.env["utm.source"].create(
            {"name": old.name, "company_id": company.id}
        )
        self.assertNotEqual(
            old.name, new.name, "should be changed by utm.mixin _get_unique_names"
        )
        new.name = old.name
        self.assertEqual(
            old.name, new.name, "should be allowed by modified _sql_constraints"
        )
