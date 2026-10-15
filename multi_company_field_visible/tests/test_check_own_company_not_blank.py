# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestCheckOwnCompanyNotBlank(TransactionCase):
    def test_creating_a_company_does_not_crash(self):
        # Core's own res.company.create() creates the company's own contact
        # through res.partner.create(), which -- as an internal side effect
        # of base_multi_company's company_id inverse -- briefly writes a
        # blank company_ids on that very partner before it has a company to
        # point to. That transient, internal state must not be rejected by
        # this module's "own company can't be blank" safety net.
        env = self.env(
            context=dict(self.env.context, test_multi_company_field_visible=True)
        )
        company = env["res.company"].create({"name": "Check Blank Co"})
        self.assertEqual(company.partner_id.sudo().company_ids, company)
