# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CrmTag(models.Model):

    _inherit = "crm.tag"

    company_id = fields.Many2one(
        "res.company",
        "Company",
        default=lambda self: self.env.company,
        ondelete="cascade",
    )
