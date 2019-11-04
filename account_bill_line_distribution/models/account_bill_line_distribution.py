# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountInvoiceLineDistribution(models.Model):
    _name = 'account.invoice.line.distribution'
    _description = "Distribution Line of Vendor Bill Line"
    _rec_name = 'company_id'

    @api.multi
    def _default_company_id(self):
        return self.invoice_line_id.company_id

    percent = fields.Float(string="Percentage", default=0.00)
    invoice_line_id = fields.Many2one('account.invoice.line',
                                      string="Bill Line",
                                      readonly=True)
    company_id = fields.Many2one('res.company', string="Company",
                                 default=_default_company_id)

    _sql_constraints = \
        [('line_company_uniq', 'UNIQUE (invoice_line_id, company_id)',
          'You cannot have the same company twice in a distribution!')]
