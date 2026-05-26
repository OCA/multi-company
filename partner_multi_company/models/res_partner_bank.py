# Copyright 2026 Tecnativa - Christian Ramos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

from odoo import fields, models
from odoo.models import BaseModel


def _to_company_ids(companies):
    if isinstance(companies, BaseModel):
        return companies.ids
    elif isinstance(companies, (list | tuple | str)):
        return companies
    return [companies]


def _check_companies_domain_parent_of(self, companies):
    """A `_check_company_domain` function that lets a record be used if
    any company in record.company_ids is a parent of any of the given companies.
    """
    if isinstance(companies, str):
        return [
            "|",
            ("company_ids", "parent_of", companies),
            ("company_ids", "=", False),
        ]
    companies = [id_ for id_ in _to_company_ids(companies) if id_]
    if not companies:
        return []
    return [
        "|",
        (
            "company_ids",
            "in",
            [
                int(parent)
                for rec in self.env["res.company"].sudo().browse(companies)
                for parent in rec.parent_path.split("/")[:-1]
            ],
        ),
        ("company_ids", "=", False),
    ]


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"
    _check_company_auto = True
    _check_company_domain = _check_companies_domain_parent_of

    company_ids = fields.Many2many(
        string="Companies",
        related="partner_id.company_ids",
    )
