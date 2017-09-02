# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, models
from odoo.http import request


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _signup_create_user(self, values):
        values.update({
            'company_id': request.website.company_id.id,
            'company_ids': [(6, 0, request.website.company_id.ids)],
        })
        return super(ResUsers, self)._signup_create_user(values)
