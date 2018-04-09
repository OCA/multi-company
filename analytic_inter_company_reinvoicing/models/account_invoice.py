# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.model
    def _prepare_invoice_line_data(
            self, dest_inv_type, dest_invoice_vals,
            dest_company, src_line, src_company_partner_id):
        values = super(AccountInvoice, self)._prepare_invoice_line_data(
            dest_inv_type, dest_invoice_vals,
            dest_company, src_line, src_company_partner_id,
        )

        base_line = self.env['account.invoice.line'].search([
            ('reinvoice_line_id', '=', src_line.id),
            ('reinvoice_analytic_account_id', '!=', False)
        ], limit=1)
        if base_line:
            values['account_analytic_id'] = \
                base_line.reinvoice_analytic_account_id.id
        return values
