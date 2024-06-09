# Copyright (C) 2024 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    priority_intercompany_pricelist_id = fields.Many2one(
        comodel_name="product.pricelist",
        string="Priority Intercompany Pricelist",
        domain=lambda self: self._domain_priority_intercompany_pricelist(),
    )

    def _domain_priority_intercompany_pricelist(self):
        domain = []
        interco_pricelists = (
            self.env["product.pricelist"]
            .sudo()
            .search(
                [
                    ("is_intercompany_supplier", "=", "True"),
                    ("company_id", "!=", self.id),
                ]
            )
        )
        restricted_pricelists = interco_pricelists.filtered(
            lambda x, s=self: s.country_id in x.country_group_ids.country_ids
            or not x.country_group_ids
        )
        if restricted_pricelists:
            domain.append(("id", "in", restricted_pricelists.ids))
        return domain
