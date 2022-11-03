# Copyright 2022 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ResPartner(models.Model):
    _inherit = ["res.partner", "company.check.mixin"]
    _name = "res.partner"

    def _allowed_company_get_fields_to_check(self):
        return ["sale_order_ids", "invoice_ids"]
