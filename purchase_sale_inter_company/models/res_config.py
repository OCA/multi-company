# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class InterCompanyRulesConfig(models.TransientModel):

    _inherit = 'res.config.settings'

    intercompany_overwrite_purchase_price = fields.Boolean(
        related='company_id.intercompany_overwrite_purchase_price',
        string="Synchronise prices on SO confirmation",
        help='If unchecked intercompany sale order line prices will be '
        'compared with their respective purchase order line prices and '
        'an error will be raised if not equal. If selected, no '
        'comparison will be done and SO line price will be copied to the '
        'PO line price.',
        readonly=False,
    )
    so_from_po = fields.Boolean(
        related='company_id.so_from_po',
        string="Create Sale Orders when buying to this company",
        help='Generate a Sale Order when a Purchase Order with this company '
        'as supplier is created.\n The intercompany user must at least be '
        'Sale User.',
        readonly=False,
    )
    po_from_so = fields.Boolean(
        related='company_id.po_from_so',
        string="Create Purchase Orders when selling to this company",
        help='Generate a Purchase Order when a Sale Order with this company '
        'as customer is created.\n The intercompany user must at least be '
        'Purchase User.',
        readonly=False,
    )
    sale_auto_validation = fields.Boolean(
        related='company_id.sale_auto_validation',
        string='Sale Orders Auto Validation',
        help='When a Sale Order is created by a multi company rule for '
             'this company, it will automatically validate it.',
        readonly=False,
    )
    purchase_auto_validation = fields.Boolean(
        related='company_id.purchase_auto_validation',
        string='Purchase Orders Auto Validation',
        help='When a Purchase Order is created by a multi company rule for '
             'this company, it will automatically validate it.',
        readonly=False,
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        related='company_id.warehouse_id',
        string='Warehouse for Sale Orders',
        help='Default value to set on Sale Orders that will be created '
        'based on Purchase Orders made to this company.',
        readonly=False,
    )
    po_picking_type_id = fields.Many2one(
        comodel_name='stock.picking.type',
        related='company_id.po_picking_type_id',
        string='Picking type for Purchase Orders',
        help='Default value to set on Purchase Orders ("Deliver To" field) that '
        'will be created based on Sale Orders made to this company.',
        readonly=False,
    )
    intercompany_user_id = fields.Many2one(
        comodel_name='res.users',
        related='company_id.intercompany_user_id',
        string='Intercompany User',
        readonly=False,
    )
