# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Warehouse For Sale Orders",
        help="Default value to set on Sale Orders that "
        "will be created based on Purchase Orders made to this company",
    )
