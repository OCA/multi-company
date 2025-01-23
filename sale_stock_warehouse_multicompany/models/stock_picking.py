# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_allowed_companies(self):
        return (
            self.company_id
            | self.sudo().move_ids.sale_line_id.company_id
            | self.sudo().sale_id.company_id
        ) & self.env.user.company_ids

    def button_validate(self):
        # Extend access to all related SO companies because many modules hook
        # _action_done on stock.picking and access the related sales order.
        # Without this, we would get an AccessError
        self = self.with_context(allowed_company_ids=self._get_allowed_companies().ids)
        return super().button_validate()
