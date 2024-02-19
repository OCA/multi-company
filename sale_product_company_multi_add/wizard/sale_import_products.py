# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class SaleImportProducts(models.TransientModel):
    _inherit = "sale.import.products"

    sale_company_id = fields.Many2one("res.company")

    @api.model
    def default_get(self, default_fields):
        res = super().default_get(default_fields)
        sale = self.env["sale.order"].browse(self.env.context.get("active_id", False))
        res["sale_company_id"] = sale.company_id.id
        return res
