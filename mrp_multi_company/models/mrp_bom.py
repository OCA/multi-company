# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MrpBom(models.Model):
    _name = "mrp.bom"
    _inherit = ["multi.company.abstract", "mrp.bom"]

    company_ids = fields.Many2many(
        related="product_tmpl_id.company_ids",
        comodel_name="res.company",
        store=True,
        relation="mrp_bom_res_company_rel",
        column1="mrp_bom_id",
        column2="res_company_id",
        ondelete="restrict",
    )
