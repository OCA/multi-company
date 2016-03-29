# -*- coding: utf-8 -*-
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    company_ids = fields.Many2many(
        'res.company',
        string='Companies',
        help="Company to which the sales team belongs")
    company_id = fields.Many2one(default=False)
