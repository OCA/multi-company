# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class IrActionsReportXml(models.Model):

    _inherit = 'ir.actions.report.xml'

    @api.model
    def _default_company(self):
        return self.env['res.company']._company_default_get('res.partner')

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', default=_default_company)
