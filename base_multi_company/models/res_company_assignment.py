# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, tools


class ResCompanyAssignment(models.Model):

    _name = 'res.company.assignment'
    _auto = False

    name = fields.Char()

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s
                AS SELECT id, name
                FROM res_company;
        """ % (self._table))
