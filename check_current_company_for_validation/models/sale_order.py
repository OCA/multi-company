# Copyright 2024 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = ["sale.order", "check.current.company.mixin"]
    _name = "sale.order"

    def action_confirm(self):
        self.check_current_company()
        return super().action_confirm()
