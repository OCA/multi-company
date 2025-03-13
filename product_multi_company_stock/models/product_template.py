# Copyright 2025 ForgeFlow S.L.
#   (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

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
