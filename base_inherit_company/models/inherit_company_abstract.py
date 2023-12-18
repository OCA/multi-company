#  Copyright 2023 Simone Rubino - Aion Tech
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class InheritCompanyAbstract(models.AbstractModel):
    _inherit = "multi.company.abstract"
    _name = "inherit.company.abstract"
    _description = "Inherit Company Abstract"

    @api.model
    def _get_inherit_companies(self, companies):
        """Get companies descending from the oldest parent of `companies`."""
        inherit_companies = self.env["res.company"].browse()
        companies = companies._origin or companies
        for company in companies:
            # Get the oldest parent
            while company:
                parent_company = company.parent_id
                if parent_company:
                    company = parent_company
                    continue
                else:
                    # When `company` has no parent, it is the oldest parent
                    parent_company = company
                    break
            else:
                parent_company = company

            if parent_company:
                children_companies = self.env["res.company"].search(
                    [
                        ("id", "child_of", parent_company.id),
                    ],
                )
            else:
                children_companies = self.env["res.company"].browse()

            inherit_companies |= parent_company | children_companies
        return inherit_companies

    def _update_inherit_companies(self, companies):
        """Assign to `company_ids` the companies in the family of `companies`."""
        inherit_companies = self._get_inherit_companies(companies)
        if inherit_companies != self.company_ids:
            self.company_ids = inherit_companies

    @api.onchange(
        "company_ids",
    )
    def onchange_inherit_company_ids(self):
        """Assign to `company_ids` the companies in the family of `company_ids`."""
        companies = self.company_ids
        if companies:
            self._update_inherit_companies(companies)

    @api.onchange(
        "company_id",
    )
    def onchange_inherit_company_id(self):
        """Assign to `company_ids` the companies in the family of `company_id`."""
        company = self.company_id
        if company:
            self._update_inherit_companies(company)
