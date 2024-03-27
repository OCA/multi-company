# Copyright 2023 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class InterCompanyRulesConfig(models.TransientModel):

    _inherit = "res.config.settings"

    po_from_so = fields.Boolean(
        related="company_id.po_from_so",
        string="Create Purchase Orders when selling to this company",
        help="Generate a Purchase Order when a Sale Order with this company "
        "as customer is created.\n The intercompany user must at least be "
        "Purchase User.",
        readonly=False,
    )
    purchase_auto_validation = fields.Boolean(
        related="company_id.purchase_auto_validation",
        string="Purchase Orders Auto Validation",
        help="When a Purchase Order is created by a multi company rule for "
        "this company, it will automatically validate it.",
        readonly=False,
    )
    intercompany_purchase_user_id = fields.Many2one(
        comodel_name="res.users",
        related="company_id.intercompany_purchase_user_id",
        string="Intercompany Purchase User",
        help="User used to create the Purchase order arising from a sale "
        "order in another company.",
        readonly=False,
    )
