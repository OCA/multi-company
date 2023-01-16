# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"
    # we add the 'product_id' in the order see comment in product_supplierinfo_group.py
    _order = "sequence, product_id, min_qty DESC, price, id"

    intercompany_pricelist_id = fields.Many2one(
        related="group_id.intercompany_pricelist_id",
        store=True,
    )

    def unlink(self):
        groups = self.group_id.filtered(lambda r: r.intercompany_pricelist_id)
        result = super().unlink()

        # Remove empty groups
        groups.filtered(lambda s: not s.supplierinfo_ids).with_context(
            automatic_intercompany_sync=True
        ).unlink()
        return result

    def _fields_for_group_match(self):
        result = super()._fields_for_group_match()
        result["intercompany_pricelist_id"] = "intercompany_pricelist_id"
        return result
