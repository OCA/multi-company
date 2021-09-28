# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_sale_order_data(
        self, name, partner, dest_company, direct_delivery_address
    ):
        res = super()._prepare_sale_order_data(
            name, partner, dest_company, direct_delivery_address
        )
        pricelist = self.env["product.pricelist"].search(
            [
                ("company_id", "=", dest_company.id),
                ("is_intercompany_supplier", "=", True),
            ]
        )
        if not len(pricelist) == 1:
            raise UserError(
                _("Company %s do not have an intercompany pricelist configured"),
                dest_company.name,
            )
        else:
            res["pricelist_id"] = pricelist.id
        return res
