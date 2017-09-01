# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, models, _
from odoo.http import request
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _signup_create_user(self, values):
        values['company_id'] = request.website.company_id.id
        return super(ResUsers, self)._signup_create_user(values)
