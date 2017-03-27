# -*- coding: utf-8 -*-
# © 2015 Akretion (http://www.akretion.com)
# Sébastien BEAU <sebastien.beau@akretion.com>
# Chafique Delli <chafique.delli@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    holding_company_id = fields.Many2one(
        'res.company',
        related='section_id.holding_company_id',
        string='Holding Company for Invoicing',
        readonly=True,
        copy=False,
        store=True)

    holding_invoice_id = fields.Many2one(
        'account.invoice',
        string='Holding Invoice',
        copy=False,
        readonly=True)

    invoice_state = fields.Selection([
        ('none', 'Not Applicable'),
        ('not_ready', 'Not Ready'),
        ('invoiceable', 'Invoiceable'),
        ('pending', 'Pending'),
        ('invoiced', 'Invoiced'),
        ], string='Invoice State',
        copy=False,
        compute='_compute_invoice_state',
        store=True)

    @api.multi
    @api.depends('shipped', 'section_id.holding_company_id')
    def _compute_invoice_state(self):
        # Note for perf issue the 'holding_invoice_id.state' is not set here
        # as a dependency. Indeed the dependency is manually triggered when
        # the holding_invoice is generated or the state is changed
        for sale in self:
            if not sale.section_id.holding_company_id:
                sale.invoice_state = 'none'
            elif sale.holding_invoice_id:
                if sale.holding_invoice_id.state in ('open', 'paid'):
                    sale.invoice_state = 'invoiced'
                else:
                    sale.invoice_state = 'pending'
            elif sale.shipped:
                sale.invoice_state = 'invoiceable'
            else:
                sale.invoice_state = 'not_ready'

    @api.multi
    def _set_invoice_state(self, state):
        if self:
            self._cr.execute("""UPDATE sale_order
                SET invoice_state=%s
                WHERE id in %s""", (state, tuple(self.ids)))
            self.invalidate_cache()

    @api.onchange('section_id')
    def onchange_section_id(self):
        if self.section_id and self.section_id.holding_company_id:
            self.order_policy = 'manual'
