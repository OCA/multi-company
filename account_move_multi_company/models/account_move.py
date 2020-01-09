# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.multi
    def post(self, invoice=False):
        dedicated_companies_vals = {}
        journal_entry_transfer = self.env['account.move']
        transfer_lines = []
        lines_to_reconcile = []
        for move in self:
            for line in move.line_ids.sorted(key=lambda r: r.id):
                if line.transfer_to_company_id:
                    transfer_lines.append((0, 0, {
                        'account_id': line.account_id.id,
                        'partner_id': line.partner_id.id,
                        'credit': line.debit}))

                    transfer_lines.append((0, 0, {
                        'account_id':
                        self.env.user.company_id.
                        due_from_account_id.id,
                        'partner_id': line.transfer_to_company_id.
                        partner_id.id,
                        'debit': line.debit}))

                    if line.transfer_to_company_id not in\
                            dedicated_companies_vals:
                        dedicated_companies_vals[line.transfer_to_company_id]\
                            = {'journal_id': line.transfer_to_company_id.
                                due_fromto_payment_journal_id.id,
                                'company_id': line.transfer_to_company_id.id,
                                'line_ids': [(0, 0,
                                              {'account_id':
                                               line.transfer_to_company_id.
                                               due_to_account_id.id,
                                               'partner_id':
                                               line.company_id.
                                               partner_id.id,
                                               'credit': line.debit}),
                                             (0, 0,
                                              {'account_id':
                                               self.env['account.account'].
                                               sudo().search(
                                                   [('code', '=', line.
                                                     account_id.code),
                                                    ('company_id', '=',
                                                     line.
                                                     transfer_to_company_id.id
                                                     )],
                                                   limit=1).id, 'partner_id':
                                               line.partner_id.id,
                                               'debit': line.debit})]}
                    else:
                        dedicated_companies_vals[
                            line.transfer_to_company_id]['line_ids'].append(
                            (0, 0, {'account_id': line.transfer_to_company_id.
                                    due_to_account_id.id, 'partner_id':
                                    line.company_id.partner_id.id,
                                    'credit': line.debit}))
                        dedicated_companies_vals[
                            line.transfer_to_company_id]['line_ids'].append(
                            (0, 0, {'account_id':
                                    self.env['account.account'].sudo().
                                    search(
                                            [('code',
                                              '=', line.account_id.code),
                                             ('company_id', '=',
                                              line.company_id.id)],
                                        limit=1).id,
                                    'partner_id': line.partner_id.id,
                                    'debit': line.debit}))
                    lines_to_reconcile.append(line)

            # Journal entry in main company for employees who worked for other
            # companies of the group.
            if self.env.user.company_id.due_fromto_payment_journal_id \
                    and transfer_lines:
                journal_entry_transfer = self.env['account.move'].create({
                    'journal_id':
                    self.env.user.company_id.
                    due_fromto_payment_journal_id.id,
                    'line_ids': transfer_lines
                })
                self += journal_entry_transfer

                transfer_lines = journal_entry_transfer.line_ids.\
                    filtered("credit").sorted(key=lambda r: r.id)

                for (line, rec_line) in zip(transfer_lines,
                                            lines_to_reconcile):
                    (line + rec_line).reconcile()

                # Journal Entry for each dedicated company
                dedicated_company_move = self.env['account.move'].sudo()
                for transfer_to_company_id in dedicated_companies_vals:
                    dedicated_company_move += self.env['account.move'].sudo().\
                        create(dedicated_companies_vals[
                               transfer_to_company_id])
                self += dedicated_company_move

        return super(AccountMove, self).post()

    def _post_validate(self):
        # Override to prevent ValidationError
        # Method in odoo/addons/account/models/account_move line 357
        return True


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    transfer_to_company_id = fields.Many2one(
        'res.company', string='Transfer to')
