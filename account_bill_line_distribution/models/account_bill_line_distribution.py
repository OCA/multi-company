# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError


class AccountInvoiceLineDistribution(models.Model):
    _name = "account.invoice.line.distribution"
    _description = "Distribution Line of Vendor Bill Line"
    _rec_name = "company_id"

    @api.model
    def _get_default_company_id(self):
        company_id = self.env.context.get("company_id")
        return (
            company_id
            or self.invoice_line_id.company_id.id
            or self.invoice_line_id.move_id.company_id.id
            or self.env.user.company_id.id
        )

    percent = fields.Float(string="Percentage")
    amount = fields.Float(string="Amount")
    invoice_line_id = fields.Many2one(
        "account.move.line", string="Bill Line", ondelete="cascade", check_company=True
    )
    company_id = fields.Many2one(
        "res.company", string="Company", required=True, default=_get_default_company_id
    )

    #    REMOVE: Due to duplicate invoiceline record for the move line for journal entry
    #    _sql_constraints = \
    #        [('line_company_uniq', 'UNIQUE (invoice_line_id, company_id)',
    #          'You cannot have the same company twice in a distribution!')]

    @api.constrains("invoice_line_id","company_id")
    def _check_unique_company_distribution(self):
        for rec in self:
            distribution_lines = rec.search_count([('invoice_line_id','=',rec.invoice_line_id.id),
                                                    ('company_id','=',rec.company_id.id),
                                                    ('id','!=',rec.id)])
            if distribution_lines:
                raise ValidationError(_('You cannot have the same company twice in a distribution!'))
            
    @api.onchange("percent")
    def _onchange_percent_total(self):
        for dist in self:
            dist.amount = (dist.invoice_line_id.price_subtotal * dist.percent) / 100

    #
    @api.onchange("amount")
    def _onchange_amount_total(self):
        for dist in self:
            if dist.invoice_line_id.price_subtotal != 0.00:
                dist.percent = (dist.amount / dist.invoice_line_id.price_subtotal) * 100
            else:
                dist.percent = 0.00
