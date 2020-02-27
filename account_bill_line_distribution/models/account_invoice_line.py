# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    distribution_ids = fields.One2many(
        'account.invoice.line.distribution', 'invoice_line_id',
        string='Distribution', copy=True)

    def get_default_distribution(self):
        return {'percent': 100.00,
                'company_id':
                    self.env.context.get('company_id') or
                    self.company_id.id or
                    self.invoice_id.company_id.id or
                    self.env.user.company_id.id}

    @api.model
    def create(self, vals):
        if 'distribution_ids' not in vals or not vals['distribution_ids']:
            if vals.get('company_id', False):
                vals.update({
                    'distribution_ids': [(0, 0, self.
                            with_context({'company_id': vals['company_id']}).
                            get_default_distribution())]})
            else:
                vals.update({
                            'distribution_ids':
                            [(0, 0, self.get_default_distribution())]})
        return super().create(vals)

    @api.constrains('distribution_ids')
    def _check_percentage(self):
        for line in self:
            if line.distribution_ids:
                total = 0.00
                for dist_id in line.distribution_ids:
                    total += dist_id.percent
                if total != 100.00:
                    raise ValidationError(_(
                        "The distribution for {} does not total to 100%.").
                        format(line.name))

    @api.onchange('distribution_ids')
    def _onchange_distribution_ids_percent(self):
        percentage = 0.00
        if self.distribution_ids:
            i = 0
            for dist in self.distribution_ids:
                if dist.company_id != self.env.user.company_id:
                    percentage += dist.percent
                else:
                    index = i
                i += 1
            if 'index' in locals():
                self.distribution_ids[index].percent = 100.00 - percentage
        else:
            self.distribution_ids = [self.get_default_distribution()]
