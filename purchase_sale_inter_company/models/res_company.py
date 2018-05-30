# -*- coding: utf-8 -*-
# © 2013-Today Odoo SA
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class ResCompany(models.Model):

    _inherit = 'res.company'

    sale_auto_validation = fields.Boolean(
        string='Sale Auto Validation',
        help="When a Sale Order is created by a multi company rule "
             "for this company, it will automatically validate it",
        default=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse For Sale Orders',
        help="Default value to set on Sale Orders that "
        "will be created based on Purchase Orders made to this company")
    update_intercompany_purchase_price = fields.Boolean(
        help=("If an intercompany sale order item has a different price than "
              "the originating purchase item, update the purchase item "
              "automatically. If disabled, just log the price differences on "
              "the purchase order (and don't allow to confirm the sales "
              "order)."),
        default=True)
