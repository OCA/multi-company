# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    pricelist_item_id = fields.Many2one(
        comodel_name="product.pricelist.item",
        string="Pricelist Rule",
        ondelete="set null",
        readonly=True,
        index=True,
        copy=False,
        help="The Vendor's price is linked to a specific intercompany pricelist item",
    )
