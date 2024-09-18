# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.osv import expression


class MassMailing(models.Model):
    _inherit = "mailing.mailing"

    company_id = fields.Many2one("res.company", "Company")

    def _get_recipients(self):
        res_ids = super()._get_recipients()
        if self.company_id:
            records = self.env[self.mailing_model_real].browse(res_ids)
            res_ids = records.filtered(
                lambda r: not r.company_id or r.company_id == self.company_id
            ).ids
        return res_ids

    def _compute_total(self):
        res = super()._compute_total()
        for mailing in self:
            if mailing.company_id:
                domain = expression.AND(
                    [
                        mailing._parse_mailing_domain(),
                        [
                            "|",
                            ("company_id", "=", mailing.company_id.id),
                            ("company_id", "=", False),
                        ],
                    ]
                )
                total = self.env[mailing.mailing_model_real].search_count(domain)
                if total and mailing.ab_testing_enabled and mailing.ab_testing_pc < 100:
                    total = max(int(total / 100.0 * mailing.ab_testing_pc), 1)
                mailing.total = total
        return res
