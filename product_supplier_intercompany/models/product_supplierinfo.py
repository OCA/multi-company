# © 2019 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import Warning as UserError


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    intercompany_pricelist_id = fields.Many2one(
        comodel_name="product.pricelist",
    )

    pricelist_item_id = fields.Many2one(comodel_name="product.pricelist.item")

    def _check_intercompany_supplier(self):
        if not self._context.get("automatic_intercompany_sync"):
            for record in self:
                if record.mapped("intercompany_pricelist_id"):
                    raise UserError(
                        _(
                            "This supplier info can not be edited as it's "
                            "linked to an intercompany 'sale' pricelist.\n "
                            "Please modify the information on the 'sale' "
                            "pricelist"
                        )
                    )

    def write(self, vals):
        self._check_intercompany_supplier()
        return super(ProductSupplierinfo, self).write(vals)

    @api.model
    def create(self, vals):
        record = super(ProductSupplierinfo, self).create(vals)
        record._check_intercompany_supplier()
        return record

    def unlink(self):
        self._check_intercompany_supplier()
        return super(ProductSupplierinfo, self).unlink()
