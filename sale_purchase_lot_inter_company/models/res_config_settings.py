# Copyright (c) 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# @author Guillaume MASSON <guillaume.masson@groupevoltaire.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    propagated_serial_number_so_po = fields.Boolean(
        string="Lots/Serial Numbers are propagated from sales in this company to "
        "purchase orders",
        related="company_id.propagated_serial_number_so_po",
        readonly=False,
    )
