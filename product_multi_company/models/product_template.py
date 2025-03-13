# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = ["multi.company.abstract", "product.template"]
    _name = "product.template"
    _description = "Product Template (Multi-Company)"

    @api.constrains("company_ids")
    def _check_company_ids(self):
        for record in self:
            if record.company_ids:
                quants = self.env["stock.quant"].search(
                    [
                        ("product_id", "in", record.product_variant_ids.ids),
                        ("company_id", "not in", record.company_ids.ids),
                        ("quantity", "!=", 0),
                        ("location_id.usage", "=", "internal"),
                    ]
                )
                if quants:
                    companies = quants.mapped("company_id")
                    company_names = ", ".join(companies.mapped("name"))
                    raise UserError(
                        _(
                            "Cannot remove the following companies because "
                            "there are stock quantities associated with them: %s"
                        )
                        % company_names
                    )
                moves = self.env["stock.move"].search(
                    [
                        ("product_id", "in", record.product_variant_ids.ids),
                        ("company_id", "not in", record.company_ids.ids),
                    ]
                )
                if moves:
                    companies = moves.mapped("company_id")
                    company_names = ", ".join(companies.mapped("name"))
                    raise UserError(
                        _(
                            "Cannot remove the following companies because "
                            "there are stock moves associated with them: %s"
                        )
                        % company_names
                    )
