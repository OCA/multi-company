# -*- coding: utf-8 -*-
# © 2016 Akretion (http://www.akretion.com)
# Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError
import logging
_logger = logging.getLogger(__name__)


class SaleMakeInvoice(models.TransientModel):
    _inherit = 'sale.make.invoice'

    def _get_info(self):
        if not self._context.get('active_ids'):
            return {}
        sales = self.env['sale.order'].browse(self._context['active_ids'])
        sections = {}
        for sale in sales:
            if sections.get(sale.section_id):
                sections[sale.section_id] |= sale
            else:
                sections[sale.section_id] = sale
        for section, sales in sections.items():
            if section.holding_company_id:
                if len(sections) != 1:
                    return {
                        'error':
                            _('Holding Invoice must be invoiced per section')}
                if section.holding_invoice_generated_by == 'holding':
                    user = self.env['res.users'].browse(self._uid)
                    if user.company_id == section.holding_company_id:
                        return {
                            'error': (
                                _('The sale order %s must be invoiced from '
                                  'the holding company')
                                % (', '.join(sales.mapped('name'))))}
                else:
                    not_invoiceable = self.env['sale.order'].browse(False)
                    for sale in sales:
                        if sale.invoice_state != 'invoiceable':
                            not_invoiceable |= sale
                    if not_invoiceable:
                        return {
                            'error': (
                                _('The sale order %s can not be invoiced')
                                % (', '.join(not_invoiceable.mapped('name'))))}
                return {'section': section}
        return {}

    def _compute_error(self):
        msg = self._get_info()
        return msg.get('error')

    def _compute_section(self):
        msg = self._get_info()
        if msg.get('section'):
            return msg['section']
        else:
            return self.env['crm.case.section'].browse(False)

    error = fields.Text(default=_compute_error, readonly=True)
    section_id = fields.Many2one(
        'crm.case.section',
        string="Sale Section",
        default=_compute_section,
        readonly=True)

    @api.multi
    def make_invoices(self):
        self.ensure_one()
        if self.error:
            raise UserError(self.error)
        if self.section_id:
            domain = [('id', 'in', self._context['active_ids'])]
            invoices = self.env['holding.invoicing'].\
                _generate_invoice(domain, date_invoice=self.invoice_date)
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
        else:
            return super(SaleMakeInvoice, self).make_invoices()
