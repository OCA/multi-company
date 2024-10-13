# Copyright (C) 2017-Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, models

from .product_product import _SUFFIX_LENGTH


class ResCompany(models.Model):
    _inherit = "res.company"

    # Overload Section
    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._create_default_code_sequence()
        return res

    # Custom Section
    def _create_default_code_sequence(self):
        IrSequence = self.env["ir.sequence"]
        for company in self:
            IrSequence.create(
                {
                    "name": "%s - Default Code for Products" % (company.code),
                    "code": "product_product.default_code",
                    "company_id": company.id,
                    "prefix": "%s-" % (company.code),
                    "padding": _SUFFIX_LENGTH,
                }
            )
