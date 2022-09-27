# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    force_backorder = fields.Boolean(string="Force backorder", default=False)
    force_no_backorder = fields.Boolean(string="Force No backorder", default=False)

    @api.model
    def default_get(self, fields):
        res = super(StockBackorderConfirmation, self).default_get(fields)
        picking = self.env["stock.picking"].browse(
            self.env.context.get("picking_id", False)
        )
        sale_order = self.env["sale.order"]
        if picking.picking_type_code == "incoming":
            sale_order = sale_order.sudo().search([(
                'name', '=', picking.purchase_id.partner_ref
            )])
        if not picking or not sale_order:
            return res
        is_intercompany = self.env["res.company"].search(
            [("partner_id", "=", picking.partner_id.id)]
        ) or self.env["res.company"].search(
            [("partner_id", "=", picking.partner_id.parent_id.id)]
        )
        if is_intercompany and is_intercompany.sync_picking \
                and picking.picking_type_code == "incoming":
            if sale_order.shipping_status == "completed":
                res.update({"force_no_backorder": True})
            else:
                res.update({"force_backorder": True})
        return res
