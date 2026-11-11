# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    def _explode_intercompany_kit(self, product, kit_qty):
        bom_qty = product.uom_id._compute_quantity(kit_qty, self.product_uom_id)
        _, bom_lines = self.explode(product, bom_qty / self.product_qty)
        return {bom_line: bom_line_data["qty"] for bom_line, bom_line_data in bom_lines}
