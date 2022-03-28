# © 2019 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models
from odoo.exceptions import Warning as UserError


class IntercompanySupplierinfoMixin(models.AbstractModel):
    _name = "intercompany.supplierinfo.mixin"

    def check_intercompany_pricelist(self):
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


class ProductSupplierinfo(models.Model):
    _inherit = ["product.supplierinfo", "intercompany.supplierinfo.mixin"]
    _name = "product.supplierinfo"

    intercompany_pricelist_id = fields.Many2one(
        comodel_name="product.pricelist",
    )

    pricelist_item_id = fields.Many2one(comodel_name="product.pricelist.item")

    def check_access_rule(self, operation):
        super().check_access_rule(operation)
        if operation in ("write", "create", "unlink"):
            self.check_intercompany_pricelist()
