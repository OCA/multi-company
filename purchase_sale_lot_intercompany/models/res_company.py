# Copyright 2023 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# @author Guillaume MASSON <guillaume.masson@groupevoltaire.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    propagated_serial_number = fields.Boolean(
        string="Lots/Serial Numbers are propogated in this company"
    )
