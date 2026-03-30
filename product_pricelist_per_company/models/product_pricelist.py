# Copyright (C) 2026-Today: GRAP (http://www.grap.coop)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    company_id = fields.Many2one(default=lambda x: x._default_company_id())

    def _default_company_id(self):
        return self.env.company

    @api.constrains("company_id")
    def _check_company_id(self):
        pricelists = self.filtered(lambda x: not x.company_id)
        if pricelists:
            raise ValidationError(
                _(
                    "You can not create a global pricelist"
                    " that is not related to any company:"
                    " \n\n- %(pricelist_names)s",
                    pricelist_names=",\n- ".join(pricelists.mapped("name")),
                )
            )
