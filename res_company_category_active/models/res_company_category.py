# Copyright (C) 2026 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class ResCompanyCategory(models.Model):
    _inherit = "res.company.category"

    # Overwrite default section to filter only active companies
    @api.depends(
        "company_ids.active", "company_ids.category_id", "child_ids.company_qty"
    )
    def _compute_company_qty(self):
        for category in self:
            if category.type == "normal":
                category.company_qty = len(
                    category.company_ids.filtered(lambda x: x.active)
                )
            else:
                category.company_qty = sum(category.mapped("child_ids.company_qty"))
