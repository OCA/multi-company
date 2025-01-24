# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartnerCategory(models.Model):

    _inherit = "res.partner.category"
    _check_company_auto = True

    company_id = fields.Many2one(
        "res.company",
        "Company",
        ondelete="cascade",
    )

    parent_id = fields.Many2one(check_company=True)
