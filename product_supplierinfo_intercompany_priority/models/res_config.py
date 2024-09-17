# Copyright (C) 2024 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class InterCompanyRulesConfig(models.TransientModel):
    _inherit = "res.config.settings"

    priority_intercompany_pricelist_id = fields.Many2one(
        comodel_name="product.pricelist",
        related="company_id.priority_intercompany_pricelist_id",
        string="Priority Intercompany Pricelist",
        help="The pricelist will be the default one for intercompany purchases.",
        readonly=False,
    )
