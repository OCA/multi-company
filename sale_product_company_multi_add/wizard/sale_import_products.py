# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import fields, models


class SaleImportProducts(models.TransientModel):
    _inherit = "sale.import.products"

    sale_company_id = fields.Many2one("res.company", compute="_compute_sale_company_id")

    def _compute_sale_company_id(self):
        so_obj = self.env["sale.order"]
        for wizard in self:
            sale = so_obj.browse(self.env.context.get("active_id", False))
            wizard.sale_company_id = sale.company_id
