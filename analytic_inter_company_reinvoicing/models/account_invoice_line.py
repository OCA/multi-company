# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError


class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    reinvoice_analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string="Reinvoice to analytic account",
        ondelete='restrict',
        domain="[('company_id', '!=', company_id)]",
    )
    reinvoice_line_id = fields.Many2one(
        comodel_name='account.invoice.line',
        string="Reinvoice line",
        readonly=True,
        copy=False,
    )

    @api.multi
    def write(self, values):
        self._check_update_reinvoiced_lines()
        return super(AccountInvoiceLine, self).write(values)

    @api.multi
    def unlink(self):
        self._check_update_reinvoiced_lines()
        return super(AccountInvoiceLine, self).unlink()

    @api.multi
    def _check_update_reinvoiced_lines(self):
        for rec in self:
            if rec.reinvoice_line_id:
                raise UserError(
                    _("You can't modify/delete an invoice line if it has "
                      "been reinvoiced.")
                )

    @api.onchange(
        'reinvoice_analytic_account_id',
        'company_id'
    )
    def _onchange_reinvoice_analytic_account(self):
        if self.reinvoice_analytic_account_id and self.company_id:
            self.account_id = self.company_id.reinvoice_waiting_account_id
