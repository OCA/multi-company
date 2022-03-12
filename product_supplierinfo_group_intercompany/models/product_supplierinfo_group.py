# Copyright 2022 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductSupplierinfoGroup(models.Model):
    _inherit = ["product.supplierinfo.group", "intercompany.supplierinfo.mixin"]
    _name = "product.supplierinfo.group"

    intercompany_pricelist_id = fields.Many2one("product.pricelist")

    _sql_constraints = [
        (
            "intercopany_pricelist_uniq",
            "unique(intercompany_pricelist_id, product_tmpl_id, product_id)",
            "Product can have only one group per intercompany pricelist",
        )
    ]

    def check_access_rule(self, operation):
        if operation in ("create", "unlink"):
            self.check_intercompany_pricelist()
        super().check_access_rule(operation)

    def check_field_access_rights(self, operation, fields):
        if operation == "write" and fields != ["sequence"]:
            self.check_intercompany_pricelist()
        return super().check_field_access_rights(operation, fields)

    def _sync_sequence(self):
        for record in self:
            if record.intercompany_pricelist_id:
                record.sequence = record.intercompany_pricelist_id.supplier_sequence

    def write(self, vals):
        super().write(vals)
        if "sequence" in vals:
            self._sync_sequence()
        return True

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._sync_sequence()
        return record
