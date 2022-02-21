# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models
from odoo.osv import expression


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    def unlink(self):
        groups = self.supplierinfo_group_id.filtered(
            lambda r: r.intercompany_pricelist_id
        )
        result = super().unlink()
        self._cascade_unlink_to_group(groups)
        return result

    def _cascade_unlink_to_group(self, groups):
        to_unlink = self.env["product.supplierinfo.group"]
        for rec in groups:
            if not rec.supplierinfo_ids:
                to_unlink += rec
        to_unlink.with_context(automatic_intercompany_sync=True).unlink()

    def _get_group_domain(self, vals):
        result = expression.AND(
            [
                super()._get_group_domain(vals),
                [
                    (
                        "intercompany_pricelist_id",
                        "=",
                        bool(self.intercompany_pricelist_id)
                        and self.intercompany_pricelist_id.id,
                    )
                ],
            ]
        )
        return result
