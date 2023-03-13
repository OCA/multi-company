# Copyright 2023 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# @author Guillaume MASSON <guillaume.masson@groupevoltaire.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

class StockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    def get_inter_company_lot(self, company):
        inter_company_lots = self.env["stock.production.lot"]
        for lot in self:
            inter_company_lot = (
                self.env["stock.production.lot"]
                .sudo()
                .search(
                    [
                        ("name", "=", lot.name),
                        ("product_id", "=", lot.product_id.id),
                        ("company_id", "=", company.id),
                    ]
                )
            )
            if not inter_company_lot and company.propagated_serial_number:
                inter_company_lot = (
                    self.env["stock.production.lot"]
                    .with_context(no_propagate=True)
                    .sudo()
                    .create(
                        {
                            "name": lot.name,
                            "product_id": lot.product_id.id,
                            "product_uom_id": lot.product_uom_id.id,
                            "ref": lot.ref,
                            "company_id": company.id,
                        }
                    )
                )
            inter_company_lots |= inter_company_lot
        return inter_company_lots
    

    
