# © 2019 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import Warning as UserError


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    is_intercompany_supplier = fields.Boolean(
        default=False, inverse="_inverse_intercompany_supplier"
    )

    generated_supplierinfo_ids = fields.One2many(
        comodel_name="product.supplierinfo",
        inverse_name="intercompany_pricelist_id",
    )

    @api.constrains("company_id", "is_intercompany_supplier")
    def _check_required_company_for_intercompany(self):
        for record in self:
            if record.is_intercompany_supplier and not record.company_id:
                raise UserError(_("The company is required for intercompany pricelist"))

    def _inverse_intercompany_supplier(self):
        for rec in self:
            if rec.is_intercompany_supplier:
                rec._active_intercompany()
            else:
                rec._unactive_intercompany()

    def _active_intercompany(self):
        for rec in self:
            if rec.is_intercompany_supplier:
                if not rec.company_id:
                    raise UserError(
                        _("Intercompany pricelist must belong to a company")
                    )
                self.item_ids._init_supplier_info()

    def _unactive_intercompany(self):
        self.sudo().with_context(automatic_intercompany_sync=True).mapped(
            "generated_supplierinfo_ids"
        ).unlink()
