# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrActionsReport(models.Model):

    _inherit = 'ir.actions.report'

    company_id = fields.Many2one('res.company')
