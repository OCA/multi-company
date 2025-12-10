# Copyright 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestMcViewRestriction(TransactionCase):
    def setUp(self):
        super().setUp()

        model_partner = self.env["ir.model"].search(
            [("model", "=", "res.partner")], limit=1
        )
        self.restriction = self.env["multicompany.view.restriction"].create(
            {
                "model_id": model_partner.id,
            }
        )
        self.view_id = self.env.ref("base.view_partner_form").id
        self.company_1 = self.env.ref("base.main_company")
        self.company_2 = self.env["res.company"].create({"name": "Comp B"})

    def test_view_restriction_blocks_multicompany(self):
        ctx = dict(
            self.env.context, allowed_company_ids=[self.company_1.id, self.company_2.id]
        )
        with self.assertRaises(UserError) as m:
            self.env["res.partner"].with_context(**ctx)._get_view(view_id=self.view_id)
        self.assertIn("when several companies are active.", m.exception.args[0])

    def test_view_allowed_single_company(self):
        ctx = dict(self.env.context, allowed_company_ids=[self.company_1.id])
        self.env["res.partner"].with_context(**ctx)._get_view(view_id=self.view_id)
