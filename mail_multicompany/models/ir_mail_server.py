# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields


class IrMailServer(models.Model):

    _inherit = "ir.mail_server"

    company_id = fields.Many2one('res.company', 'Company')
