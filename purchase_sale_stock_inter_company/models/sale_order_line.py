# Copyright 2025 Tecnativa - Carlos Lopez
from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_location_final(self):
        partner = self.order_id.partner_id
        commercial_partner = partner.commercial_partner_id
        Company = self.env["res.company"].sudo()
        dest_company = Company.search(
            [("partner_id", "parent_of", commercial_partner.id)], limit=1
        )
        # Check if the partner belongs to another company and use its customer location
        # instead of the partner's shipping_id location.
        if (
            dest_company
            and dest_company != self.company_id
            and partner != self.order_id.partner_shipping_id
        ):
            return partner.with_company(self.company_id).property_stock_customer
        return super()._get_location_final()
