from odoo import Command, fields, models
from odoo.tools import config


class StockPicking(models.Model):
    _inherit = "stock.picking"

    counterpart_of_picking_id = fields.Many2one("stock.picking", check_company=False)

    def _create_counterpart_picking(self):
        companies = self.env["res.company"].sudo().search([])
        partners = {cp.partner_id: cp for cp in companies}
        picking = self.env["stock.picking"]
        if self.partner_id in partners:
            company = partners[self.partner_id]
            # Switch to target company context before creating picking
            picking_model = self.env["stock.picking"].sudo().with_company(company)
            vals = self._get_counterpart_picking_vals(company)
            # Create picking in correct company context
            picking = picking_model.create(vals)
            # Confirm picking in the same company context
            picking.action_confirm()
        return picking

    def _get_counterpart_picking_vals(self, company):
        # Get warehouse and picking type in correct company context
        warehouse = False
        with_company = self.env["stock.warehouse"].sudo().with_company(company)
        ptype = False

        if company.intercompany_in_type_id:
            ptype = company.intercompany_in_type_id
            if ptype.warehouse_id:
                warehouse = ptype.warehouse_id

        if not warehouse:
            warehouse = with_company.search([("company_id", "=", company.id)], limit=1)

        if not ptype:
            ptype = warehouse.in_type_id

        # Ensure locations belong to correct company
        location_dest = ptype.default_location_dest_id or warehouse.lot_stock_id
        supplier_location = self.env.ref("stock.stock_location_suppliers")

        move_ids, move_line_ids = self._check_company_consistency(company, ptype)

        return {
            "partner_id": self.env.user.company_id.partner_id.id,
            "company_id": company.id,
            "origin": self.name,
            "picking_type_id": ptype.id,
            "state": "draft",
            "location_id": supplier_location.id,
            "location_dest_id": location_dest.id,
            "counterpart_of_picking_id": self.id,
            "move_ids": move_ids,
            "move_line_ids": move_line_ids,
            "scheduled_date": self.scheduled_date,
            "priority": self.priority,
        }

    def _check_company_consistency(self, company, picking_type):
        # Ensure supplier location has no company set
        supplier_location = self.env.ref("stock.stock_location_suppliers")
        if supplier_location.company_id:
            supplier_location.sudo().company_id = False

        common_vals = {
            "company_id": company.id,
            "location_id": supplier_location.id,
            "picking_type_id": picking_type.id,
        }

        # Create moves with correct company context
        move_ids = []
        for sm in self.move_ids.sudo():
            move_vals = sm.with_company(company).copy_data(
                dict(
                    common_vals,
                    counterpart_of_move_id=sm.id,
                    picking_type_id=picking_type.id,
                )
            )[0]
            move_ids.append(Command.create(move_vals))

        # Create move lines with correct company context
        move_line_ids = []
        for ln in self.move_line_ids.sudo():
            line_vals = ln.with_company(company).copy_data(
                dict(
                    common_vals,
                    move_id=False,
                    counterpart_of_line_id=ln.id,
                    picking_type_id=picking_type.id,
                )
            )[0]
            move_line_ids.append(Command.create(line_vals))

        return move_ids, move_line_ids

    def _action_done(self):
        test_condition = not config["test_enable"] or (
            config["test_enable"] and self.env.context.get("test_stock_intercompany")
        )
        if not test_condition:
            return super()._action_done()
        counterparts = []
        for picking in self:
            if picking.location_dest_id.usage == "customer":
                counterpart = picking._create_counterpart_picking()
                counterparts.append((picking, counterpart))
        res = super()._action_done()
        for picking, counterpart in counterparts:
            picking._finalize_counterpart_picking(counterpart)
        return res

    def _finalize_counterpart_picking(self, counterpart_picking):
        """hook to finalize required steps on the counterpart picking after the initial
        outgoing picking is done"""
