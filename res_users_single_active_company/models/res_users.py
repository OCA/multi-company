# Copyright 2026 XXP LLC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ResUsers(models.Model):
    _inherit = "res.users"

    allow_single_company = fields.Boolean(
        string="Single Active Company",
        copy=True,
        help="Keep one active company for this user.",
    )

    def _single_active_company_limit_active(self):
        """
        Returns:
            True if the user must keep one active company, False otherwise.
        """
        self.ensure_one()
        return bool(
            self.allow_single_company and self.has_group("base.group_multi_company")
        )

    def _get_company_to_activate(self, company):
        """
        Get the company to activate.

        args:
            company: The company to activate.
        Returns:
            The company to activate.
        """
        if isinstance(company, int):
            company = self.env["res.company"].browse(company)
        if not company or len(company) != 1:
            raise UserError(_("Select an allowed company."))
        return company

    @api.model
    def apply_single_active_company(self, company):
        """
        RPC entry for the warning dialog.

        args:
            company: The company to activate.
        Returns:
            True if the company is activated, False otherwise.
        """
        return self._apply_single_active_company(company)

    @api.model
    def _apply_single_active_company(self, company):
        """
        Set the current user's company when the limit is active.

        args:
            company: The company to activate.
        Returns:
            True if the company is activated, False otherwise.
        """
        user = self.env.user
        if not user._single_active_company_limit_active():
            raise UserError(_("Single Active Company is not enabled for this user."))
        company = self._get_company_to_activate(company)
        if company not in user.company_ids:
            raise UserError(_("Select an allowed company."))
        user.write({"company_id": company.id})
        return True
