# -*- coding: utf-8 -*-
# © 2015 Oihane Crucelaegui
# © 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html.html

from odoo import api, models


class ResPartner(models.Model):

    _inherit = ["multi.company.abstract", "res.partner"]
    _name = 'res.partner'
    _description = 'Partners (Multi-Company)'

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

    @api.model_cr_context
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
