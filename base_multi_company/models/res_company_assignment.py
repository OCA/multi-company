# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResCompanyAssignment(models.Model):

    _name = 'res.company.assignment'
    _auto = False

    name = fields.Char()
