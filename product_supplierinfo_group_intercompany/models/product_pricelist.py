# Copyright 2022 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    supplier_sequence = fields.Integer(
        default=-1,
        help=(
            "Force the supplier sequence, use a negative value if you want to "
            "have this supplier in first position, use a big positif value "
            "if you want to be the last"
        ),
    )
    supplier_group_ids = fields.One2many(
        "product.supplierinfo.group", "intercompany_pricelist_id", "Supplier Group"
    )

    def write(self, vals):
        super().write(vals)
        if "supplier_sequence" in vals:
            for record in self:
                record.supplier_group_ids._sync_sequence()
        return True
