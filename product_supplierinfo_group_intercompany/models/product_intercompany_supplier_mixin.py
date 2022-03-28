# Copyright 2022 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ProductIntercompanySupplierMixin(models.AbstractModel):
    _inherit = "product.intercompany.supplier.mixin"

    @api.onchange("supplierinfo_group_ids")
    def onchange_supplierinfo_group_ids(self):
        for record in self.sudo():
            for idx, group in enumerate(
                record.supplierinfo_group_ids.sorted("sequence")
            ):
                group.sequence = idx
            record.supplierinfo_group_ids._sync_sequence()
