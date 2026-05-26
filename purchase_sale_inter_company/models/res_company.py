# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    so_from_po = fields.Boolean(
        string="Create Sale Orders when buying to this company",
        help="Generate a Sale Order when a Purchase Order with this company "
        "as supplier is created.\n The intercompany user must at least be "
        "Sale User.",
    )
    sale_auto_validation = fields.Boolean(
        string="Sale Orders Auto Validation",
        default=True,
        help="When a Sale Order is created by a multi company rule for "
        "this company, it will automatically validate it.",
    )
    intercompany_sale_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Intercompany Sale User",
    )
