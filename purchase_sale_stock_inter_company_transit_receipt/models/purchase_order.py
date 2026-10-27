# Copyright 2026 Akretion
# @author Guillaume MASSON <guillaume.masson@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _requires_transit_receipt(self):
        company = self.company_id
        return super()._requires_transit_receipt() or bool(
            company.sync_picking
            and company.sync_picking_transit_receipt
            and self.sudo().partner_id.commercial_partner_id.ref_company_ids.filtered(
                "so_from_po"
            )
        )
