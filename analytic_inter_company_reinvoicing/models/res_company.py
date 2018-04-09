# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class ResCompany(models.Model):

    _inherit = 'res.company'

    reinvoice_waiting_account_id = fields.Many2one(
        comodel_name='account.account',
        string="Reinvoice Waiting Account",
    )
