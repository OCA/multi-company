# Copyright (C) 2023-Today: GRAP (<http://www.grap.coop/>)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    is_favorite = fields.Boolean(
        string="Favorite",
        company_dependent=True,
        help="If this field is unchecked, the category will"
        " be hidden when searching category in a drop-down list"
        " like in the product form view.",
    )

    @api.onchange("parent_id")
    def onchange_parent_id_favorite(self):
        if self.parent_id:
            self.is_favorite = self.parent_id.is_favorite

    @api.model_create_multi
    def create(self, vals_list):
        categories = super().create(vals_list)
        # Configure is_favorite for all the other companies
        company_ids = (
            self.env["res.company"]
            .with_context(active_test=False)
            .search([("id", "!=", self.env.company.id)])
            .ids
        )
        for company_id in company_ids:
            for category in categories:
                ctx_category = category.with_company(company_id)
                if ctx_category.parent_id:
                    # We inherit the contextual configuration of the parent category, if any
                    ctx_category.is_favorite = ctx_category.parent_id.is_favorite
                else:
                    # Otherwise, we set the same setting as the current one
                    ctx_category.is_favorite = category.is_favorite
        return categories

    def write(self, vals):
        if "is_favorite" in vals:
            children = self.search([("id", "child_of", self.ids)]).filtered(
                lambda x: x.id not in self.ids
            )
            super(ProductCategory, children).write({"is_favorite": vals["is_favorite"]})
        return super().write(vals)

    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = list(args or [])
        if not args or not any(
            [x[0] == "is_favorite" for x in args if getattr(x, "__getitem__", False)]
        ):
            args += [("is_favorite", "=", True)]
        return super()._name_search(
            name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid
        )
