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
                            if inv.type == 'in_invoice':
                                # Debit line for the amount due from the other
                                # company
                                self.get_from_lines(from_lines,
                                                    invoice_line_id,
                                                    inv, amount, distrib,
                                                    True)
                            elif inv.type == 'in_refund':
                                # Credit line for the amount due from
                                # the other company
                                self.get_from_lines(from_lines,
                                                    invoice_line_id,
                                                    inv, amount, distrib,
                                                    False)
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
                                'date': inv.date_invoice,
                                'journal_id':
                                    company.due_fromto_payment_journal_id.id,
                                'state': 'draft',
                                'ref': inv.company_id.name + ': ' + inv.number,
                                'company_id': company.id}
                            # Credit company "Due_To" Account with debit
                            # amount from its previous "Due from" Account entry
                            for line in from_lines:
                                if inv.type == 'in_invoice':
                                    if line['partner_id'] == company.\
                                            partner_id.id:
                                        self.get_to_lines(to_lines, line,
                                                          company, inv, True)
                                elif inv.type == 'in_refund':
                                    if line['partner_id'] == company.\
                                            partner_id.id:
                                        self.get_to_lines(to_lines, line,
                                                          company, inv, False)
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

    @api.multi
    @api.returns('self')
    def refund(self, date_invoice=None, date=None,
               description=None, journal_id=None):
        # account/models/account_invoice.py line 1536
        # clears the distributions in the original VB
        dist_obj = self.env['account.invoice.line.distribution']
        res = super().refund(date_invoice, date, description, journal_id)
        index = 0
        for line_id in self.invoice_line_ids:
            for dist_id in line_id.distribution_ids:
                if dist_id.company_id != res.invoice_line_ids[index].\
                        distribution_ids.company_id:
                    dist_obj.create({
                        'company_id': dist_id.company_id.id,
                        'percent': dist_id.percent,
                        'amount': dist_id.amount,
                        'invoice_line_id': res.invoice_line_ids[index].id})
                    res.invoice_line_ids[index].\
                        _onchange_distribution_ids_percent()
            index += 1
        return res

    def get_from_lines(self, from_lines, invoice_line_id,
                       invoice_id, amount, distribution, is_invoice):
        if is_invoice:
            from_lines.append({
                'name': invoice_line_id.name,
                'debit': amount,
                'account_id':
                    invoice_id.company_id.due_from_account_id.id,
                'partner_id':
                    distribution.company_id.partner_id.id,
                'inv_line': invoice_line_id.id})
            # Credit line for the current company
            from_lines.append({
                'name': invoice_line_id.name,
                'credit': amount,
                'account_id':
                    invoice_line_id.account_id.id,
                'partner_id':
                    invoice_id.company_id.partner_id.id,
                'inv_line': invoice_line_id.id})
        else:
            from_lines.append({
                'name': invoice_line_id.name,
                'credit': amount,
                'account_id':
                    invoice_id.company_id.due_from_account_id.id,
                'partner_id':
                    distribution.company_id.partner_id.id,
                'inv_line': invoice_line_id.id})
            # Debit line for the current company
            from_lines.append({
                'name': invoice_line_id.name,
                'debit': amount,
                'account_id':
                    invoice_line_id.account_id.id,
                'partner_id':
                    invoice_id.company_id.partner_id.id,
                'inv_line': invoice_line_id.id})

    def get_to_lines(self, to_lines, line, company, invoice_id, is_invoice):
        if is_invoice:
            to_lines.append({
                'name': line['name'],
                'credit': line['debit'],
                'account_id': company.
                due_to_account_id.id,
                'partner_id': invoice_id.
                company_id.partner_id.id,
                'inv_line': line['inv_line']
            })
            line_account = self.\
                env['account.invoice.line'].\
                browse(line['inv_line']).account_id
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
                'partner_id': invoice_id.partner_id.id,
                'inv_line': line['inv_line']
            })
        else:
            to_lines.append({
                'name': line['name'],
                'debit': line['credit'],
                'account_id': company.
                due_to_account_id.id,
                'partner_id': invoice_id.
                company_id.partner_id.id,
                'inv_line': line['inv_line']
            })
            line_account = self.\
                env['account.invoice.line'].\
                browse(line['inv_line']).account_id
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
                'credit': line['credit'],
                'account_id': new_account.id,
                'partner_id': invoice_id.partner_id.id,
                'inv_line': line['inv_line']
            })
