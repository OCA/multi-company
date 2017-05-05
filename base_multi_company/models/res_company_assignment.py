# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResCompanyAssignment(models.Model):
    """ This model circumvents company domains to allow assignments.

    Normally when using a multi company setup, you are restricted to seeing
    only records owned by the company your user is operating under
    (`user.company_id`). This creates a catch 22 with multi-company records,
    because in order to assign to another company you have to be able to view
    that company.
    """

    _name = 'res.company.assignment'
    _auto = False

    name = fields.Char()
