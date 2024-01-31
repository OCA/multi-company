# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    sale_company_id = fields.Many2one("res.company", string="Selling Company")

    @api.model
    def _commercial_fields(self):
        return super()._commercial_fields() + ["sale_company_id"]
