# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv.expression import AND


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    company_ids = fields.Many2many(
        comodel_name="res.company",
        string="Companies",
        help="This view is specific to these companies.",
    )

    @api.model
    def _get_inheriting_views_domain(self):
        domain = super()._get_inheriting_views_domain() or []

        # Website later removes ('active', '=', True)
        # leave orphan prefix operators and produce invalid domains.
        # Prevent that by removing it here.
        if self.env.context.get("website_id"):
            domain = [leaf for leaf in domain if "active" not in leaf]

        company_domain = [
            "|",
            ("company_ids", "=", False),
            ("company_ids", "in", self.env.company.ids),
        ]

        if not domain:
            return company_domain

        return AND([domain, company_domain])
