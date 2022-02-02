# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _get_intercompany_pricelist(self, partner, dest_company):
        if partner.property_product_pricelist.is_intercompany_supplier:
            return partner.property_product_pricelist
        else:
            pricelist = self.env["product.pricelist"].search(
                [
                    ("company_id", "=", dest_company.id),
                    ("is_intercompany_supplier", "=", True),
                ]
            )
            if len(pricelist) == 0:
                raise UserError(
                    _(
                        (
                            "The Company {} do not have an intercompany pricelist "
                            "configured.\nPlease contact them and ask them to "
                            "active the option on the pricelist"
                        ).format(dest_company.name)
                    )
                )
            else:
                # Note in case that there is several pricelist that match we take
                # the first one and the user will change it manually if needed
                return fields.first(pricelist)

    def _prepare_sale_order_data(
        self, name, partner, dest_company, direct_delivery_address
    ):
        res = super()._prepare_sale_order_data(
            name, partner, dest_company, direct_delivery_address
        )
        res["pricelist_id"] = self._get_intercompany_pricelist(partner, dest_company).id
        return res
