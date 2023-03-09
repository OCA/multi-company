# Copyright 2023 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    po_from_so = fields.Boolean(
        string="Create Purchase Orders when selling to this company",
        help="Generate a Purchase Order when a Sale Order with this company "
        "as customer is created.\n The intercompany user must at least be "
        "Purchase User.",
    )
    purchase_auto_validation = fields.Boolean(
        string="Purchase Orders Auto Validation",
        default=True,
        help="When a Purchase Order is created by a multi company rule for "
        "this company, it will automatically validate it.",
    )
    intercompany_purchase_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Intercompany Purchase User",
    )
