from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _create_counterpart_picking(self):
        companies = self.env["res.company"].sudo().search([])
        partners = {cp.partner_id: cp for cp in companies}
        if self.partner_id in partners:
            company = partners[self.partner_id]
            warehouse = False
            if company.intercompany_in_type_id.warehouse_id:
                warehouse = company.intercompany_in_type_id.warehouse_id
            else:
                warehouse = (
                    self.env["stock.warehouse"]
                    .sudo()
                    .search([("company_id", "=", company.id)], limit=1)
                )
            vals = {
                "partner_id": self.env.user.company_id.partner_id.id,
                "company_id": company.id,
                "picking_type_id": company.intercompany_in_type_id.id
                or warehouse.in_type_id.id,
                "state": "draft",
                "location_id": self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": warehouse.lot_stock_id.id,
            }
            new_picking_vals = self.sudo().copy_data(default=vals)
            picking = self.env["stock.picking"].sudo().create(new_picking_vals)
            picking.action_confirm()
            return picking

    # override of method from stock module
    def _action_done(self):
        counterparts = []
        for picking in self:
            if picking.location_dest_id.usage == "customer":
                counterpart = picking._create_counterpart_picking()
                counterparts.append((picking, counterpart))
        res = super(StockPicking, self)._action_done()
        for picking, counterpart in counterparts:
            picking._finalize_counterpart_picking(counterpart)
        return res

    def _finalize_counterpart_picking(self, counterpart_picking):
        """hook to finalize required steps on the counterpart picking after the initial
        outgoing picking is done"""
