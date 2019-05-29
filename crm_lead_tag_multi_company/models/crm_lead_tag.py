# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CrmLeadTag(models.Model):

    _inherit = 'crm.lead.tag'

    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'crm.lead.tag'
        ),
        ondelete='cascade',
    )
