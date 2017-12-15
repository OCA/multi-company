# -*- coding: utf-8 -*-
# Copyright 2015 ACSONE SA/NV.
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class AccountAccountType(models.Model):
    _inherit = 'account.account.type'

    company_id = fields.Many2one('res.company', string='Company')
