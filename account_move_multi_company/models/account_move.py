# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def prepare_other_company_move_line_values(
            self, line, account=False, partner=False, keep=False):
        if keep:
            debit = line.debit
            credit = line.credit
        else:
            debit = line.credit
            credit = line.debit
        return {
            'name': line.name,
            'account_id':
                account and account.id or
                line.transfer_to_company_id.due_to_account_id.id,
            'partner_id':
                partner and partner.id or line.company_id.partner_id.id,
            'debit': debit,
            'credit': credit,
        }

    def prepare_company_move_line_values(
            self, line, transfer_lines):
        transfer_lines.append((0, 0, {
            'name': line.name,
            'account_id': line.account_id.id,
            'partner_id': line.partner_id.id,
            'debit': line.credit,
            'credit': line.debit}))
        transfer_lines.append((0, 0, {
            'name': line.name,
            'account_id':
                self.env.user.company_id.due_from_account_id.id,
            'partner_id':
                line.transfer_to_company_id.partner_id.id,
            'debit': line.debit,
            'credit': line.credit}))

    @api.multi
    def post(self, invoice=False):
        res = super().post(invoice)
        dedicated_companies_vals = {}
        journal_entry_transfer = self.env['account.move']
        transfer_lines = []
        lines_to_reconcile = []
        for move in self:
            for line in move.line_ids.sorted(key=lambda r: r.id):
                if line.transfer_to_company_id:
                    company_id = line.transfer_to_company_id.id
                    # Add the lines for the current company journal entry
                    self.prepare_company_move_line_values(line, transfer_lines)
                    if line.transfer_to_company_id.id not in\
                            dedicated_companies_vals:
                        account = \
                            self.env['account.account'].sudo().with_context(
                                force_company=company_id).search([
                                    ('code', '=', line.account_id.code),
                                    ('company_id', '=', company_id)],
                                limit=1)
                        # Add the lines for the other company journal entry
                        dedicated_companies_vals[
                            line.transfer_to_company_id.id] = {
                            'date': move.date,
                            'ref': move.ref,
                            'journal_id':
                                line.transfer_to_company_id.
                                due_fromto_payment_journal_id.id,
                            'company_id': company_id,
                            'line_ids': [
                                (0, 0,
                                 self.prepare_other_company_move_line_values(
                                     line)),
                                (0, 0,
                                 self.prepare_other_company_move_line_values(
                                     line, account, line.partner_id, True))]}
                    else:
                        # Update the lines for the other company journal entry
                        dedicated_companies_vals[
                            line.transfer_to_company_id.id]['line_ids'].append(
                            (0, 0,
                             self.prepare_other_company_move_line_values(line)
                             ))
                        account = \
                            self.env['account.account'].sudo().with_context(
                                force_company=company_id).search([
                                    ('code', '=', line.account_id.code),
                                    ('company_id', '=', company_id)],
                                limit=1)
                        dedicated_companies_vals[
                            line.transfer_to_company_id.id]['line_ids'].append(
                            (0, 0,
                             self.prepare_other_company_move_line_values(
                                 line, account, line.partner_id, True)
                             ))
                    lines_to_reconcile.append(line)

            # Create, post and reconcile the entries in the current company
            if self.env.user.company_id.due_fromto_payment_journal_id \
                    and transfer_lines:
                journal_id = \
                    self.env.user.company_id.due_fromto_payment_journal_id.id
                journal_entry_transfer = self.env['account.move'].create({
                    'date': move.date,
                    'ref': move.ref,
                    'journal_id': journal_id,
                    'line_ids': transfer_lines})
                journal_entry_transfer.post()

                transfer_lines = journal_entry_transfer.line_ids.filtered(
                    lambda l:
                    l.account_id != l.company_id.due_from_account_id).\
                    sorted(key=lambda r: r.id)

                # Reconcile the entries
                for (line, rec_line) in \
                        zip(transfer_lines, lines_to_reconcile):
                    if line.account_id.reconcile:
                        (line + rec_line).reconcile()

                # Create and post the entries for the other companies
                dedicated_company_move = self.env['account.move'].sudo()
                for company_id in dedicated_companies_vals:
                    dedicated_company_move += \
                        self.env['account.move'].sudo().with_context(
                            force_company=company_id).create(
                            dedicated_companies_vals[company_id])
                # TODO: Determine the conditions to auto-post this entry
                # Left in draft to set analytic information
                # dedicated_company_move.post()
        return res
