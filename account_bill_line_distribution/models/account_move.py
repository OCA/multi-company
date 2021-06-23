# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _, SUPERUSER_ID
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def prepare_due_from_move_values(self):
        return {
            'journal_id': self.company_id.due_fromto_payment_journal_id.id,
            'date': self.date,
            'state': 'draft',
            'company_id': self.company_id.id,
            'ref': self.name,
            'line_ids': False}

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for inv in self:
            # Due From
            account_move = self.env['account.move']
            from_move_value = self.prepare_due_from_move_values()
            from_lines = []
            companies = []
            amount = 0.00
            # Lines
            for invoice_line in inv.invoice_line_ids:
                for distrib in invoice_line.with_user(SUPERUSER_ID).distribution_ids:
                    # Get companies involved
                    if distrib.company_id not in companies:
                        companies.append(distrib.company_id)
                    amount = (invoice_line.price_subtotal * distrib.percent) / 100
                    if distrib.company_id != self.company_id:
                        if inv.move_type == 'in_invoice':
                            # Debit line for the amount due from the other
                            # company
                            self.get_from_lines(from_lines,
                                                invoice_line,
                                                inv, amount, distrib,
                                                True)
                        elif inv.move_type == 'in_refund':
                            # Credit line for the amount due from
                            # the other company
                            self.get_from_lines(from_lines,
                                                invoice_line,
                                                inv, amount, distrib,
                                                False)
            # Create Journal Entry in the current company
            if from_lines:
                from_move = account_move.with_context(default_move_type='entry').create(from_move_value)
                from_move.line_ids = from_lines
                from_move.action_post()

                # Due To's
                for company in companies:
                    to_lines = []
                    # Skip the current company because that has been taken
                    # care of already
                    if company.id != inv.company_id.id:
                        to_move_vals = {
                            'date': inv.date,
                            'journal_id':
                                company.due_fromto_payment_journal_id.id,
                            'state': 'draft',
                            'ref': inv.company_id.name + ': ' + inv.name,
                            'company_id': company.id}
                        # Credit company "Due_To" Account with debit
                        # amount from its previous "Due from" Account entry
                        for line in from_lines:
                            line = line[2]
                            if inv.move_type == 'in_invoice':
                                if line['partner_id'] == company.partner_id.id:
                                    self.get_to_lines(to_lines, line, company, inv, True)
                            elif inv.move_type == 'in_refund':
                                if line['partner_id'] == company.partner_id.id:
                                    self.get_to_lines(to_lines, line, company, inv, False)
                        # Create Journal Entries in the other companies
                        if to_lines:
                            to_move = account_move.with_user(SUPERUSER_ID).\
                            with_context(default_move_type='entry'
                                         ).create(to_move_vals)
                            to_move.with_company(company).line_ids = to_lines
                            to_move.action_post()
        return res

    def action_reverse(self):

        # account/models/account_invoice.py line 1536
        # clears the distributions in the original VB
        dist_obj = self.env['account.invoice.line.distribution']
        return super().action_reverse()
        # REMOVE: Auto manage in move_type: refund
        index = 0
        for line in self.invoice_line_ids:
            for dist_line in line.distribution_ids:
                if dist_line.company_id != self.invoice_line_ids[index].distribution_ids.company_id:
                    dist_obj.create({
                        'company_id': dist_line.company_id.id,
                        'percent': dist_line.percent,
                        'amount': dist_line.amount,
                        'invoice_line_id': res.invoice_line_ids[index].id})
                    res.invoice_line_ids[index].\
                        _onchange_distribution_ids_percent()
            index += 1

    def get_from_lines(self, from_lines, invoice_line_id,
                       invoice_id, amount, distribution, is_invoice):
        if is_invoice:
            from_lines.append((0, 0, {
                'name': invoice_line_id.name,
                'debit': amount,
                'account_id':
                    invoice_id.company_id.due_from_account_id.id,
                'partner_id':
                    distribution.company_id.partner_id.id}))
            # Credit line for the current company
            from_lines.append((0, 0, {
                'name': invoice_line_id.name,
                'credit': amount,
                'account_id':
                    invoice_line_id.account_id.id,
                'partner_id':
                    invoice_id.company_id.partner_id.id}))
        else:
            from_lines.append((0, 0, {
                'name': invoice_line_id.name,
                'credit': amount,
                'account_id':
                    invoice_id.company_id.due_from_account_id.id,
                'partner_id':
                    distribution.company_id.partner_id.id}))
            # Debit line for the current company
            from_lines.append((0, 0, {
                'name': invoice_line_id.name,
                'debit': amount,
                'account_id':
                    invoice_line_id.account_id.id,
                'partner_id':
                    invoice_id.company_id.partner_id.id}))

    def get_to_lines(self, to_lines, line, company, invoice_id, is_invoice):
        if is_invoice:
            to_lines.append((0, 0, {
                'name': line['name'],
                'credit': line['debit'],
                'account_id': company.due_to_account_id.id,
                'partner_id': invoice_id.
                company_id.partner_id.id,
                'company_id':company.id
            }))
            account = self.env['account.account'].browse(line['account_id'])
            # Debit Account of invoice line
            new_account = self.\
                env['account.account'].\
                with_user(SUPERUSER_ID).search([('code', '=',
                                account.code),
                               ('company_id', '=',
                                company.id)], limit=1)
            if not new_account:
                raise UserError(_("No corresponding \
                                Account for code %s\
                                in Company %s") %
                                (account.code,
                                    company.name))
            to_lines.append((0, 0, {
                'name': line['name'],
                'debit': line['debit'],
                'account_id': new_account.id,
                'partner_id': invoice_id.partner_id.id,
                'company_id':company.id
            }))
        else:
            to_lines.append((0, 0, {
                'name': line['name'],
                'debit': line['credit'],
                'account_id': company.
                due_to_account_id.id,
                'partner_id': invoice_id.
                company_id.partner_id.id,
                'company_id':company.id
            }))
            account = self.env['account.account'].browse(line['account_id'])
            # Debit Account of invoice line
            new_account = self.env['account.account'].with_user(SUPERUSER_ID).search([('code', '=', account.code),
                               ('company_id', '=', company.id)], limit=1)
            if not new_account:
                raise UserError(_("No corresponding \
                                Account for code %s\
                                in Company %s") %
                                (account.code,
                                    company.name))
            to_lines.append((0, 0, {
                'name': line['name'],
                'credit': line['credit'],
                'account_id': new_account.id,
                'partner_id': invoice_id.partner_id.id,
                'company_id':company.id
            }))
