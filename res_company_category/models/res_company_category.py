# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResCompanyCategory(models.Model):
    _name = "res.company.category"
    _description = "Company Categories"
    _order = "complete_name"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = "complete_name"
    _order = "complete_name"

    _TYPE_SELECTION = [
        ("normal", "Normal"),
        ("view", "View"),
    ]

    name = fields.Char(required=True)

    active = fields.Boolean(default=True)

    type = fields.Selection(selection=_TYPE_SELECTION, required=True, default="normal")

    parent_id = fields.Many2one(
        string="Parent Category",
        comodel_name="res.company.category",
        domain=[("type", "=", "view")],
    )

    parent_path = fields.Char(index=True, unaccent=False)

    child_ids = fields.One2many(
        string="Category Childs",
        comodel_name="res.company.category",
        inverse_name="parent_id",
    )

    company_ids = fields.One2many(
        string="Companies", comodel_name="res.company", inverse_name="category_id"
    )

    company_qty = fields.Integer(
        string="Companies Quantity",
        compute="_compute_company_qty",
        store=True,
        recursive=True,
    )

    complete_name = fields.Char(
        compute="_compute_complete_name",
        store=True,
        recursive=True,
    )

    # Compute Section
    @api.depends("parent_id.complete_name", "name")
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = "%s / %s" % (
                    category.parent_id.complete_name,
                    category.name,
                )
            else:
                category.complete_name = category.name

    @api.depends("company_ids.category_id", "child_ids.company_qty")
    def _compute_company_qty(self):
        for category in self:
            if category.type == "normal":
                category.company_qty = len(category.company_ids)
            else:
                category.company_qty = sum(category.mapped("child_ids.company_qty"))
