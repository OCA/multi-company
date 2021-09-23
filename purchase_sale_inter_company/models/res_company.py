# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = 'res.company'

    intercompany_overwrite_purchase_price = fields.Boolean(
        string="Synchronise prices on SO confirmation",
        help='If not selected intercompany sale order line prices will be '
        'compared with their respective purchase order line prices and '
        'an error will be raised if not equal. If selected, no '
        'comparison will be done and SO line price will be copied to the '
        'PO line price.',
        default=True,
    )
    so_from_po = fields.Boolean(
        string="Create Sale Orders when buying to this company",
        help='Generate a Sale Order when a Purchase Order with this company '
        'as supplier is created.\n The intercompany user must at least be '
        'Sale User.',
    )
    po_from_so = fields.Boolean(
        string="Create Purchase Orders when selling to this company",
        help='Generate a Purchase Order when a Sale Order with this company '
        'as customer is created.\n The intercompany user must at least be '
        'Purchase User.',
    )
    sale_auto_validation = fields.Boolean(
        string='Sale Orders Auto Validation',
        default=True,
        help='When a Sale Order is created by a multi company rule for '
             'this company, it will automatically validate it.',
    )
    purchase_auto_validation = fields.Boolean(
        string='Purchase Orders Auto Validation',
        default=True,
        help='When a Purchase Order is created by a multi company rule for '
             'this company, it will automatically validate it.',
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse For Sale Orders',
        help='Default value to set on Sale Orders that '
        'will be created based on Purchase Orders made to this company')
    po_picking_type_id = fields.Many2one(
        'stock.picking.type', string='Picking type for Purchase Orders',
        help='Default value to set on Purchase Orders ("Deliver To" field) that '
        'will be created based on Sale Orders made to this company.')
    intercompany_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Intercompany User',
    )
