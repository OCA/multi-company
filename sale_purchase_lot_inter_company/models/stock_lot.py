# Copyright (c) 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# @author Guillaume MASSON <guillaume.masson@groupevoltaire.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockLot(models.Model):
    _inherit = "stock.lot"

    def prepare_intercompany_lot_values(self, company):
        return {
            "name": self.name,
            "product_id": self.product_id.id,
            "company_id": company.id,
        }

    def get_inter_company_lot(self, company):
        self.ensure_one()
        lot = self.sudo().search(
            [
                ("name", "=", self.name),
                ("product_id", "=", self.product_id.id),
                ("company_id", "=", company.id),
            ]
        )
        if not lot:
            lot = self.sudo().create(self.prepare_intercompany_lot_values(company))
        return lot
