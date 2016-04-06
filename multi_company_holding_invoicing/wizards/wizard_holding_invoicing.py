# -*- coding: utf-8 -*-
# © 2016 Akretion (http://www.akretion.com)
# Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import models, fields, api, _


class InvoiceWizard(models.TransientModel):
    _name = "wizard.holding.invoicing"

    date_invoice = fields.Date(
        'Invoice Date',
        required=True,
        default=fields.Datetime.now)
    section_id = fields.Many2one(
        'crm.case.section',
        required=True)

    @api.multi
    def _get_invoice_domain(self):
        self.ensure_one()
        return [
            ('section_id', '=', self.section_id.id),
            ('invoice_state', '=', 'invoiceable'),
            ('holding_invoice_id', '=', False),
            ]

    @api.multi
    def create_invoice(self):
        for wizard in self:
            domain = wizard._get_invoice_domain()
            invoices = self.env['holding.invoicing'].\
                _generate_invoice(domain, date_invoice=self.date_invoice)
        if invoices:
            return {
                'name': _("Invoice Generated"),
                'res_model': 'account.invoice',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': self.env.ref('account.action_invoice_tree1').id,
                'view_mode': 'tree,form',
                'domain': [('id', 'in', invoices.ids)]
            }
        return True
