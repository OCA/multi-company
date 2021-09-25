# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    res_company_id = fields.One2many(
        "res.company",
        "partner_id",
        readonly=True,
        help="Effectively a One2one field to represent the corresponding res.company",
    )
    origin_company_id = fields.Many2one(
        "res.company",
        compute="_compute_origin_company_id",
        store=True,
        help="Hack field to keep the information of the 'real' company_id. "
        "That way, we can share the contact by setting company_id to null, "
        "without losing any information. If null, the contact is not shared.",
    )

    @api.depends("res_company_id", "parent_id.origin_company_id")
    def _compute_origin_company_id(self):
        for record in self:
            if record.parent_id.origin_company_id:
                record.origin_company_id = record.parent_id.origin_company_id
                record.company_id = False
            if record.res_company_id:
                record.origin_company_id = record.res_company_id
                record.company_id = False
            else:
                record.origin_company_id = False
