# Copyright 2022 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductCategory(models.Model):
    _inherit = "product.category"
    _check_company_auto = True

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        index=True,
    )
    parent_id = fields.Many2one(check_company=True)

    @api.constrains("parent_id", "company_id")
    def check_company_restriction(self):
        for record in self:
            if (
                record.parent_id.company_id
                and not record.parent_id.company_id != record.company_id
            ):
                raise UserError(
                    _(
                        "The parent category and your category %s "
                        "must belong to the same company."
                    )
                    % record.name
                )
            if record.company_id:
                for child in record.child_id:
                    if record.company_id != child.company_id:
                        if child.company_id:
                            msg = _(
                                "The category %s must be shared as the "
                                "child %s belong to company %s."
                            ) % (record.name, child.name)
                        else:
                            msg = _(
                                "The category %s must be shared as the "
                                "child %s is shared."
                            ) % (record.name, child.name)
                        raise UserError(msg)
