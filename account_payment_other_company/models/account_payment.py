# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    hide_other_journal = fields.Boolean(default=True,
                                        invisible=True)

    @api.multi
    def action_validate_invoice_payment(self):
        res = super().action_validate_invoice_payment()
        if self.other_journal_id:
            aml = self.env['account.move.line'].search([
                ('account_id', '=', self.company_id.due_to_account_id.id),
                ('payment_id', '=', self.id)
            ])
            aml.partner_id = \
                self.sudo().other_journal_id.company_id.partner_id.id
            if not self.hide_other_journal:
                account_move = self.env['account.move']
                vals = self._prepare_other_payment_values()
                move = account_move.sudo().create(vals)
                move.partner_id = self.partner_id
            move.sudo().post()
        return res

    @api.onchange('journal_id', 'payment_type')
    def _onchange_hide_other_journal(self):
        self.hide_other_journal = not (
            self.journal_id.id == self.company_id.
            due_fromto_payment_journal_id.id and
            self.payment_type == 'outbound')

    @api.multi
    def _prepare_other_payment_values(self):
        other_journal = self.env['account.journal'].sudo().\
            browse(self.other_journal_id.id)
        return {
            'journal_id': self.other_journal_id.id,
            'state': 'draft',
            'company_id': other_journal.company_id.id,
            'ref': self.id,
            'line_ids': [(0, 0, {
                'account_id': other_journal.company_id.
                due_from_account_id.id,
                'partner_id': self.company_id.partner_id.id,
                'credit': self.amount,
            }), (0, 0, {
                'account_id': other_journal.default_debit_account_id.id,
                'partner_id': self.partner_id.id,
                'debit': self.amount,
            })]
        }

    other_journal_id = fields.Many2one(
        'account.journal', string='Paid By',
        domain=[('type', 'in', ('bank', 'cash'))])
