# -*- coding: utf-8 -*-
# © 2015 Oihane Crucelaegui
# © 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html.html

from openerp import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _default_company_ids(self):
        company_model = self.env['res.company']
        return [(6, 0, company_model._company_default_get('res.partner').ids)]

    company_ids = fields.Many2many(
        comodel_name='res.company', string="Companies",
        default=_default_company_ids)
    company_id = fields.Many2one(
        comodel_name='res.company', compute="_compute_company_id", store=True,
        inverse="_inverse_company_id")

    def _amend_company_id(self, vals):
        if 'company_ids' in vals:
            if not vals['company_ids']:
                vals['company_id'] = False
            else:
                for item in vals['company_ids']:
                    if item[0] in (1, 4):
                        vals['company_id'] = item[1]
                    elif item[0] in (2, 3, 5):
                        vals['company_id'] = False
                    elif item[0] == 6:
                        if item[2]:
                            vals['company_id'] = item[2][0]
                        else:  # pragma: no cover
                            vals['company_id'] = False
        return vals

    @api.model
    def create(self, vals):
        """Neutralize the default value applied to company_id that can't be
        removed in the inheritance, and that will activate the inverse method,
        overwriting our company_ids field desired value.
        """
        self._amend_company_id(vals)
        # We must suspend security during this creation because it fails due to
        # all the mail stuff in between that confuses security rules
        obj = getattr(self, 'suspend_security', lambda: self)()
        return super(ResPartner, obj).create(vals)

    @api.multi
    @api.depends('company_ids')
    def _compute_company_id(self):
        for partner in self:
            if partner.company_id != partner.company_ids[:1]:
                partner.company_id = partner.company_ids[:1].id

    @api.multi
    def _inverse_company_id(self):
        for partner in self:
            if (partner.company_id not in partner.company_ids and
                    bool(partner.company_id) != bool(partner.company_ids)):
                partner.company_ids = ([(6, 0, partner.company_id.ids)] if
                                       partner.company_id else False)

    @api.model
    def _commercial_fields(self):
        """Add company_ids to the commercial fields that will be synced with
         childs. Ideal would be that this field is isolated from company field,
         but it involves a lot of development (default value, incoherences
         parent/child...).
        :return: List of field names to be synced.
        """
        fields = super(ResPartner, self)._commercial_fields()
        fields += ['company_ids']
        return fields
