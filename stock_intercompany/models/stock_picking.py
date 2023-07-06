from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    counterpart_of_picking_id = fields.Many2one("stock.picking", check_company=False)

    def _create_counterpart_picking(self):
        companies = self.env["res.company"].sudo().search([])
        partners = {cp.partner_id: cp for cp in companies}
        picking = self.env["stock.picking"]
        if self.partner_id in partners:
            company = partners[self.partner_id]
            vals = self._get_counterpart_picking_vals(company)
            new_picking_vals = self.sudo().copy_data(default=vals)
            picking = (
                self.env["stock.picking"]
                .sudo()
                .with_company(company)
                .create(new_picking_vals)
            )
            picking.action_confirm()
        return picking

    def _get_counterpart_picking_vals(self, company):
        if company.intercompany_in_type_id.warehouse_id:
            warehouse = company.intercompany_in_type_id.warehouse_id
        else:
            warehouse = (
                self.env["stock.warehouse"]
                .sudo()
                .search([("company_id", "=", company.id)], limit=1)
            )
        ptype = company.intercompany_in_type_id or warehouse.in_type_id
        move_ids, move_line_ids = self._check_company_consistency(company)
        return {
            "partner_id": self.env.user.company_id.partner_id.id,
            "company_id": company.id,
            "origin": self.name,
            "picking_type_id": ptype.id,
            "state": "draft",
            "location_id": self.env.ref("stock.stock_location_suppliers").id,
            "location_dest_id": warehouse.lot_stock_id.id,
            "counterpart_of_picking_id": self.id,
            "move_ids": move_ids,
            "move_line_ids": move_line_ids,
        }

    def _check_company_consistency(self, company):
        # Replace company_id by the right one to create the counterpart picking
        common_vals = {
            "company_id": company.id,
            "location_id": self.env.ref("stock.stock_location_suppliers").id,
        }
        move_ids = [
            (
                0,
                0,
                sm.with_company(company).copy_data(
                    dict(common_vals, counterpart_of_move_id=sm.id)
                )[0],
            )
            for sm in self.move_ids
        ]
        move_line_ids = [
            (
                0,
                0,
                ln.with_company(company).copy_data(
                    dict(common_vals, move_id=False, counterpart_of_line_id=ln.id)
                )[0],
            )
            for ln in self.move_line_ids
        ]
        return move_ids, move_line_ids

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
