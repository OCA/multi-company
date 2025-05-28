# Copyright 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    intercompany_mav_price_info = fields.Html(
        string="Intercompany Multi Attribute Value Info",
        compute="_compute_intercompany_mav_price_info",
    )

    intercompany_mav_pricelist_item_id = fields.Many2one(
        comodel_name="product.pricelist.item",
        string="Intercompany Pricelist Item",
        compute="_compute_intercompany_mav_pricelist_item_id",
    )

    mav_price_indication = fields.Char(
        string="Dynamic Price", compute="_compute_mav_price_indication"
    )

    def _compute_mav_price_indication(self):
        for rec in self:
            rec.mav_price_indication = ""
            if rec.intercompany_mav_pricelist_item_id:
                indication = _("Start at ")
                indication += f"{str(rec.price)} {rec.currency_id.name}"
                rec.mav_price_indication = indication

    def _get_mav_table_data(self, rule):
        data = []
        for mav_line in rule.pricelist_item_attribute_value_ids:
            line = {
                "names": " / ".join(
                    val.display_name for val in mav_line.attribute_value_ids
                ),
                "price": mav_line.additional_price,
            }
            data.append(line)
        return data

    def _compute_intercompany_mav_pricelist_item_id(self):
        for rec in self:
            rec.intercompany_mav_pricelist_item_id = False
            if rec.intercompany_pricelist_id and not rec.product_id:
                rule_id = rec.intercompany_pricelist_id.sudo()._get_product_rule(
                    rec.product_tmpl_id,
                    rec.min_qty,
                )
                rule = self.env["product.pricelist.item"].browse(rule_id)
                if (
                    rule
                    and rule.applied_on == "1_product"
                    and rule.have_additional_price
                ):
                    rec.intercompany_mav_pricelist_item_id = rule

    def _compute_intercompany_mav_price_info(self):
        for rec in self:
            rec.intercompany_mav_price_info = ""
            rule = rec.intercompany_mav_pricelist_item_id
            if rule:
                json_data = rec._get_mav_table_data(rule)
                if json_data:
                    table = "<table>"
                    table += "<tr>\n<th>Price</th>\n<th>Names</th>\n</tr>\n"
                    for idx, _line in enumerate(json_data):
                        table += "<tr>\n<td>{}</td>\n".format(json_data[idx]["price"])
                        table += "<td>{}</td>\n</tr>\n".format(json_data[idx]["names"])
                    table += "</table>"
                    rec.intercompany_mav_price_info = table

    def _get_intercompany_price(self):
        self.ensure_one()
        mav_product = self._context.get("mav_product", False)
        mav_qty = self._context.get("mav_qty", 0.0)
        price = 0
        if mav_product:
            price = self.intercompany_pricelist_id._get_product_price(
                mav_product, mav_qty
            )
        self.price = price

    def open_intercompany_mav_price_info(self):
        view = self.env.ref(
            "product_pricelist_item_multi_attribute_value_intercompany."
            "product_supplierinfo_intercompany_mav_price_info_view"
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "view_id": view.id,
            "target": "new",
        }
