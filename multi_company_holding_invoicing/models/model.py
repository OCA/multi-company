# -*- coding: utf-8 -*-
# © 2015 Akretion (http://www.akretion.com)
# Sébastien BEAU <sebastien.beau@akretion.com>
# Chafique Delli <chafique.delli@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import fields, models


class QueueJob(models.Model):
    _inherit = 'queue.job'

    holding_invoice_id = fields.Many2one('account.invoice',
                                         string='Holding Invoice',
                                         copy=False, readonly=True)
