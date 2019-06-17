# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CrmStage(models.Model):

    _inherit = "crm.stage"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        index=True,
        help="Specific company that uses this stage. "
        "Other companies will not be able to see or use this stage.",
        default=lambda self:
            self.env["res.company"]._company_default_get("crm.stage"),
    )
