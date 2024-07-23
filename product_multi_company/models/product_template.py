# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = ["multi.company.abstract", "product.template"]
    _name = "product.template"
    _description = "Product Template (Multi-Company)"

    def _get_companies_to_remove(self, new_company_ids):
        companies_to_remove = []
        for command in new_company_ids:
            if command[0] == 3:
                companies_to_remove.append(command[1])
            elif command[0] == 6:
                if not command[2]:
                    return False  # If the list is empty, it means all companies are allowed
                if self.company_ids:
                    companies_to_remove = [
                        id for id in self.company_ids.ids if id not in command[2]
                    ]
                else:
                    companies_to_remove = [
                        id
                        for id in self.env["res.company"].search([]).ids
                        if id not in command[2]
                    ]
        return companies_to_remove

    def write(self, vals):
        if "company_ids" in vals:
            new_company_ids = vals.get("company_ids", [])
            companies_to_remove = self._get_companies_to_remove(new_company_ids)
            if companies_to_remove:
                products_to_check = self.filtered(
                    lambda product: not product.company_ids
                    or any(
                        company.id in companies_to_remove
                        for company in product.company_ids
                    )
                )
                if products_to_check:
                    move = (
                        self.env["stock.move"]
                        .sudo()
                        .search(
                            [
                                (
                                    "product_id",
                                    "in",
                                    products_to_check.product_variant_ids.ids,
                                ),
                                ("company_id", "in", companies_to_remove),
                            ],
                            order=None,
                            limit=1,
                        )
                    )
                    if move:
                        raise UserError(
                            _(
                                "This product's company cannot be removed as long as "
                                "there are stock moves of it belonging "
                                "to the company being removed."
                            )
                        )
                    quant = (
                        self.env["stock.quant"]
                        .sudo()
                        .search(
                            [
                                (
                                    "product_id",
                                    "in",
                                    products_to_check.product_variant_ids.ids,
                                ),
                                ("company_id", "in", companies_to_remove),
                                ("quantity", "!=", 0),
                            ],
                            order=None,
                            limit=1,
                        )
                    )
                    if quant:
                        raise UserError(
                            _(
                                "This product's company cannot be removed as long as "
                                "there are quantities of it belonging "
                                "to the company being removed."
                            )
                        )
        return super().write(vals)
