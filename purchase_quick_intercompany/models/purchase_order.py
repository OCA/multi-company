# Copyright (C) 2023 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def add_product(self):
        res = super().add_product()
        if self.partner_id.commercial_partner_id.ref_company_ids:
            res["context"].update(
                {
                    "show_intercompany_qty": True,
                }
            )
        return res
