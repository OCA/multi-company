# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def view_consolidated_invoice(self):
        self.ensure_one()
        cons_invoices_rec = self.env['account.invoice.consolidated'].search(
            [('partner_id', '=', self.id)])
        action = self.env.ref('account_invoice_consolidated.'
                              'account_invoice_consolidated_action')
        action = action.read()[0]
        action['domain'] = [('id', 'in', cons_invoices_rec.ids)]
        return action
