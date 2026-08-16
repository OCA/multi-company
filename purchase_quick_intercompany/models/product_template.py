#  Copyright (c) Akretion 2021
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    uom_intercompany_id = fields.Many2one("uom.uom", "Intercompany Unit of Measure")
