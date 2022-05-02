# Copyright 2022 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductSupplierinfoGroup(models.Model):
    _inherit = ["product.supplierinfo.group", "intercompany.supplierinfo.mixin"]
    _name = "product.supplierinfo.group"
    # For intercompany pricelist the sequence will have the same value
    # so we have to order also based on product_id in order to apply specific rule
    # before generic rule
    _order = "sequence, product_id, id"

    intercompany_pricelist_id = fields.Many2one("product.pricelist", readonly=True)

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
        # Note
        # sequence must be writable because we need to be able to sort other group
        # product_tmpl_id must be writable because odoo always send it
        if operation == "write" and set(fields) - {"sequence", "product_tmpl_id"}:
            self.check_intercompany_pricelist()
        return super().check_field_access_rights(operation, fields)

    def _sync_sequence(self):
        if self._context.get("sync_sequence"):
            return
        for record in self.sudo():
            if record.intercompany_pricelist_id:
                record.with_context(
                    sync_sequence=True
                ).sequence = record.intercompany_pricelist_id.supplier_sequence

    def _get_changed_vals(self, vals):
        changed_vals = {}
        for key in vals:
            value = self._fields[key].convert_to_write(self[key], self)
            if value != vals[key]:
                changed_vals[key] = vals[key]
        return changed_vals

    def write(self, vals):
        for record in self:
            changed_vals = self._get_changed_vals(vals)
            if changed_vals:
                super(ProductSupplierinfoGroup, record).write(changed_vals)
                if "sequence" in vals:
                    record._sync_sequence()
        return True

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._sync_sequence()
        return record
