# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    code = fields.Char(
        copy=False,
        help="""This code is used as a common key to propagate fiscal positions to
        other companies""",
    )
