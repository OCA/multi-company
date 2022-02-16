# Copyright 2022 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductSupplierinfoGroup(models.Model):

    _inherit = "product.supplierinfo.group"

    intercompany_sequence = fields.Integer(
        compute="_compute_intercompany_sequence", store=True
    )
    intercompany_pricelist_id = fields.Many2one(
        "product.pricelist", compute="_compute_intercompany_pricelist_id", store=True
    )

    @api.depends("intercompany_pricelist_id", "sequence")
    def _compute_intercompany_sequence(self):
        for rec in self:
            if rec.intercompany_pricelist_id:
                rec.intercompany_sequence = (
                    rec.intercompany_pricelist_id.intercompany_sequence
                )
            else:
                rec.intercompany_sequence = rec.sequence

    @api.depends("supplierinfo_ids.intercompany_pricelist_id")
    def _compute_intercompany_pricelist_id(self):
        for rec in self:
            rec.intercompany_pricelist_id = (
                rec.supplierinfo_ids.intercompany_pricelist_id
            )

    def _check_sync_only(self):
        if not self._context.get("automatic_intercompany_sync"):
            for record in self:
                if record.mapped("intercompany_pricelist_id"):
                    raise UserError(
                        _(
                            "This supplier info group can not be edited as it's "
                            "linked to an intercompany 'sale' pricelist.\n "
                            "Please modify the information on the 'sale' "
                            "pricelist"
                        )
                    )

    def write(self, vals):
        if list(vals.keys()) != ["sequence"]:
            self._check_sync_only()
        return super().write(vals)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._check_sync_only()
        return record

    def unlink(self):
        self._check_sync_only()
        return super().unlink()
