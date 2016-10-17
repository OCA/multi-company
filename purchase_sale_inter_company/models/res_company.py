# -*- coding: utf-8 -*-
from openerp import api, fields, models, _, SUPERUSER_ID
from openerp.exceptions import ValidationError


class ResCompany(models.Model):

    _inherit = 'res.company'

    sale_auto_validation = fields.Boolean(
        string='Sale Auto Validation',
        help="When a Sale Order is created by a multi company rule "
             "for this company, it will automatically validate it",
        default=True)
    intercompany_user_id = fields.Many2one(
        'res.users', string='Inter Company User',
        help="Responsible user for creation of documents triggered by "
        "intercompany rules. You cannot select the administrator, because "
        "the administrator by-passes the record rules, which is a problem "
        "when Odoo reads taxes on products.")

    @api.model
    def _find_company_from_partner(self, partner_id):
        company = self.sudo().search([('partner_id', '=', partner_id)],
                                     limit=1)
        return company or False

    @api.multi
    @api.constrains('intercompany_user_id')
    def _check_intercompany_user_id(self):
        self.ensure_one()
        if self.intercompany_user_id:
            if self.intercompany_user_id.id == SUPERUSER_ID:
                raise ValidationError(_(
                    'You cannot use the administrator as the Inter Company '
                    'User, because the administrator by-passes record rules.'
                ))
            if self.intercompany_user_id.company_id != self:
                raise ValidationError(_(
                    "The Inter Company User '%s' is attached to company "
                    "'%s', so you cannot select it for company '%s'.") % (
                        self.intercompany_user_id.name,
                        self.intercompany_user_id.company_id.name,
                        self.name))
            if len(self.intercompany_user_id.company_ids) > 1:
                raise ValidationError(_(
                    "You should not select '%s' as Inter Company User "
                    "because he is allowed to switch between several "
                    "companies, so there is no warranty that he will "
                    "stay in this company.") % self.intercompany_user_id.name)
