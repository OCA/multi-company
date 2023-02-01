from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _check_company_consistency(self, company):
        # Replace company_id by the right one to create the counterpart picking
        move_lines = [
            (0, 0, line.with_company(company).copy_data()[0])
            for line in self.move_lines
        ]
        for move in move_lines:
            move[2]["company_id"] = company.id
            move[2]["location_id"] = self.env.ref("stock.stock_location_suppliers").id

        move_line_ids = [
            (0, 0, line.with_company(company).copy_data()[0])
            for line in self.move_line_ids
        ]
        for move_line in move_line_ids:
            move_line[2]["company_id"] = company.id
            move_line[2]["move_id"] = False
            move_line[2]["location_id"] = self.env.ref(
                "stock.stock_location_suppliers"
            ).id
        return move_lines, move_line_ids

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
                "origin": self.name,
                "picking_type_id": company.intercompany_in_type_id.id
                or warehouse.in_type_id.id,
                "state": "draft",
                "location_id": self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": warehouse.lot_stock_id.id,
            }
            move_lines, move_line_ids = self._check_company_consistency(company)
            vals.update(
                {
                    "move_lines": move_lines or False,
                    "move_line_ids": move_line_ids or False,
                }
            )
            new_picking_vals = self.sudo().copy_data(default=vals)
            picking = (
                self.env["stock.picking"]
                .sudo()
                .with_company(company)
                .create(new_picking_vals)
            )
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
