# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class account_register_payments(models.TransientModel):
    _inherit = "account.register.payments"
    _description = "Register Payments"

    other_journal_id = fields.Many2one(
        'account.journal', string='Paid By',
        domain=[('type', 'in', ('bank', 'cash'))])
    show_other_journal = fields.Boolean(default=False, invisible=True)
    company_id = fields.\
        Many2one('res.company', related='journal_id.company_id',
                 string='Company', readonly=True)

    @api.multi
    @api.onchange('journal_id', 'payment_type')
    def onchange_show_other_journal(self):
        for rec in self:
            res = (rec.journal_id.id == rec.company_id.
                   due_fromto_payment_journal_id.id and
                   rec.payment_type in ('outbound', 'inbound') and
                   rec.partner_type == 'supplier')
            # If False, reset the other journal
            if not res:
                rec.other_journal_id = False
            rec.show_other_journal = res

    @api.multi
    def create_payments(self):
        res = super().create_payments()
        if self.show_other_journal:
            for pay_id in res['domain'][0][2]:
                payment_id = self.env['account.payment'].browse(pay_id)
                payment_id.\
                    write({'other_journal_id': self.other_journal_id.id})
                payment_id.create_move_other_company()
        return res

    @api.model
    def default_get(self, fields):
        rec = super().default_get(fields)
        active_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')
        # Check for selected invoices ids
        if not active_ids or active_model != 'account.invoice':
            return rec
        invoices = self.env['account.invoice'].browse(active_ids)
        # Check all invoices are for suppliers
        if all(invoice.partner_id.supplier for invoice in invoices):
            rec.update({'partner_type': 'supplier'})
        return rec
