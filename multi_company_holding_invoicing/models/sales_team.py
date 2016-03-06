# -*- coding: utf-8 -*-
# © 2015 Akretion (http://www.akretion.com)
# Sébastien BEAU <sebastien.beau@akretion.com>
# Chafique Delli <chafique.delli@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import fields, models


class CrmCaseSection(models.Model):
    _inherit = 'crm.case.section'

    holding_company_id = fields.Many2one(
        'res.company', string='Holding Company for Invoicing',
        help="Select the holding company to invoice")
    holding_customer_automatic_invoice = fields.Boolean(
        string='Holding customer',
        help="Check this box to invoice automatically the holding's customers "
             "from delivery orders completed")
    holding_supplier_automatic_invoice = fields.Boolean(
        string='Holding supplier',
        help="Check this box to invoice automatically the holding's suppliers "
             "from delivery orders completed")
    holding_discount = fields.Float(string='Holding Discount (%)', default=0.0)
