# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    auto_purchase_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        string="Source Purchase Order Line",
        readonly=True,
        copy=False,
    )

    def _sync_price_unit_to_intercompany_purchase_line(self):
        """
        This method is used to sync the price unit
        of the sale order line to the price unit
        of the purchase order line in case of intercompany sale.
        It takes into account the tax inclusion/exclusion
        of both the sale order line and the purchase order line.
        """
        dest_taxes = self.auto_purchase_line_id.taxes_id
        price_unit = self.price_unit
        base_line = self._prepare_base_line_for_taxes_computation(quantity=1)
        self.env["account.tax"]._add_tax_details_in_base_line(
            base_line, self.company_id
        )
        # case where taxes in the company A are price excluded
        # but in the company B are price included
        if self.tax_id.filtered("price_include") and not dest_taxes.filtered(
            "price_include"
        ):
            price_unit = base_line["tax_details"]["raw_total_excluded_currency"]
        # case where taxes in the company A are price included
        # but in the company B are price excluded
        if not self.tax_id.filtered("price_include") and dest_taxes.filtered(
            "price_include"
        ):
            price_unit = base_line["tax_details"]["raw_total_included_currency"]
        self.auto_purchase_line_id.price_unit = price_unit
