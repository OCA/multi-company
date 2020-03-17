# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def prepare_due_from_move_values(self):
        return {
            'journal_id': self.company_id.due_fromto_payment_journal_id.id,
            'date': self.date_invoice,
            'state': 'draft',
            'company_id': self.company_id.id,
            'ref': self.number,
            'line_ids': False}

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        for inv in self:
            if inv.invoice_line_ids:
                # Due From
                account_move = self.env['account.move']
                from_move_value = self.prepare_due_from_move_values()
                from_lines = []
                companies = []
                amount = 0.00
                # Lines
                for invoice_line_id in inv.invoice_line_ids:
                    for distrib in invoice_line_id.distribution_ids:
                        # Get companies involved
                        if distrib.company_id not in companies:
                            companies.append(distrib.company_id)
                        amount = invoice_line_id.price_subtotal * \
                            distrib.percent / 100
                        if distrib.company_id != self.company_id:
                            # Debit line for the amount due from the other
                            # company
                            from_lines.append({
                                'name': invoice_line_id.name,
                                'debit': amount,
                                'account_id':
                                    inv.company_id.due_from_account_id.id,
                                'partner_id':
                                    distrib.company_id.partner_id.id})
                            # Credit line for the current company
                            from_lines.append({
                                'name': invoice_line_id.name,
                                'credit': amount,
                                'account_id':
                                    invoice_line_id.account_id.id,
                                'partner_id':
                                    inv.company_id.partner_id.id})

                    # Create Journal Entry in the current company
                    if from_lines:
                        from_move = account_move.sudo().create(from_move_value)
                        for line in from_lines:
                            line.update({'move_id': from_move.id})
                        self.env['account.move.line'].create(from_lines)
                        from_move.post()

                    # Due To's
                    for company in companies:
                        to_lines = []
                        # Skip the current company because that has been taken
                        # care of already
                        if company.id != inv.company_id.id:
                            to_move_vals = {
                                'journal_id':
                                    company.due_fromto_payment_journal_id.id,
                                'state': 'draft',
                                'ref': inv.company_id.name + ': ' + inv.number,
                                'company_id': company.id}
                            # Credit company "Due_To" Account with debit
                            # amount from its previous "Due from" Account entry
                            for line in from_lines:
                                if line['partner_id'] == company.partner_id.id:
                                    to_lines.append({
                                        'name': line['name'],
                                        'credit': line['debit'],
                                        'account_id': company.
                                        due_to_account_id.id,
                                        'partner_id': inv.
                                        company_id.partner_id.id
                                    })
                                    line_account = invoice_line_id.account_id
                                    # Debit Account of invoice line
                                    new_account = self.\
                                        env['account.account'].\
                                        sudo().search([('code', '=',
                                                        line_account.code),
                                                       ('company_id', '=',
                                                        company.id)], limit=1)
                                    if not new_account:
                                        raise UserError(_("No corresponding \
                                                          Account for code %s\
                                                           in Company %s") %
                                                        (line_account.code,
                                                         company.name))
                                    to_lines.append({
                                        'name': line['name'],
                                        'debit': line['debit'],
                                        'account_id': new_account.id,
                                        'partner_id': inv.partner_id.id
                                    })
                            # Create Journal Entries in the other companies
                            if to_lines:
                                to_move = account_move.sudo().\
                                    with_context(force_company=company.id)\
                                    .create(to_move_vals)
                                for line in to_lines:
                                    line.update({
                                        'move_id': to_move.id,
                                        'company_id': company.id
                                    })
                                self.env['account.move.line'].sudo().\
                                    with_context(force_company=company.id).\
                                    create(to_lines)
                                to_move.post()
        return res
