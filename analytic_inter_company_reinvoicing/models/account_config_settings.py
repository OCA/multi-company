# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class AccountConfigSettings(models.TransientModel):

    _inherit = 'account.config.settings'

    reinvoice_waiting_account_id = fields.Many2one(
        related='company_id.reinvoice_waiting_account_id',
    )
