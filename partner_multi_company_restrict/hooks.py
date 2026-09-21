# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command


def post_init_hook(env):
    """Scope each pre-existing company's own contact to itself.

    A company's partner is created with a blank ``company_ids`` (the
    "shared with everyone" convention used across this stack), which made
    it visible to every user regardless of company. Give it its own
    company so the existing company-scoping rules apply to it too.
    """
    for company in env["res.company"].search([]):
        if not company.partner_id.company_ids:
            company.partner_id.company_ids = [Command.link(company.id)]
