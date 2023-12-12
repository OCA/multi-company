from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    intercompany_parent_id = fields.Many2one(
        comodel_name="stock.picking",
        string="Intercompany picking that created this counterpart picking",
        copy=False,
    )
    intercompany_child_ids = fields.One2many(
        comodel_name="stock.picking",
        inverse_name="intercompany_parent_id",
        string="Intercompany pickings created by this counterpart picking",
    )

    def _create_counterpart_picking(self, mode):
        """
        Create a counterpart picking for the given picking in the given mode:
        Mode in: Create incoming from outgoing picking
        Mode out: Create outgoing from incoming picking
        """

        self.ensure_one()
        assert mode in ["in", "out"], "Invalid mode: %s" % mode

        # Skip if already has a parent to avoid looping
        # Also skip if already has children to avoid creating a duplicate
        if self.intercompany_parent_id or self.intercompany_child_ids:
            # We might want to sync if there's already a child
            return

        location = self.location_id if mode == "out" else self.location_dest_id
        usage = "customer" if mode == "in" else "supplier"

        if location.usage != usage:
            return

        company = (
            self.env["res.company"]
            .sudo()
            .search([("partner_id", "=", self.partner_id.id)], limit=1)
        )
        # Only create a picking if the recipient is a different company
        if not company or company == self.company_id:
            return

        # Restrict to the configured mode on the target company
        if company.intercompany_picking_creation_mode not in [mode, "both"]:
            return

        if not self._check_intercompany_company(company, mode):
            return

        intercompany_type = getattr(company, "intercompany_%s_type_id" % mode)

        warehouse = intercompany_type.warehouse_id or (
            self.env["stock.warehouse"]
            .sudo()
            .search([("company_id", "=", company.id)], limit=1)
        )

        # Defalut intercompany type to warehouse in/out type
        intercompany_type = intercompany_type or getattr(warehouse, "%s_type_id" % mode)

        new_picking_vals = self._prepare_counterpart_picking_vals(
            company, intercompany_type, warehouse, mode
        )
        picking = self.env["stock.picking"].sudo().create(new_picking_vals)
        picking.action_confirm()
        return picking

    def _check_intercompany_company(self, company, mode):
        """
        Hook to check if the given company is valid for the given mode.
        """
        return True

    def _prepare_counterpart_picking_vals(
        self, company, intercompany_type, warehouse, mode
    ):
        """Prepare the values to create the counterpart picking"""

        # in : suppliers -> stock
        # out: stock -> customers
        location_src = (
            self.env.ref("stock.stock_location_suppliers")
            if mode == "in"
            else warehouse.lot_stock_id
        )
        location_dest = (
            warehouse.lot_stock_id
            if mode == "in"
            else self.env.ref("stock.stock_location_customers")
        )

        vals = {
            "partner_id": self.company_id.partner_id.id,
            "company_id": company.id,
            "picking_type_id": intercompany_type.id,
            "state": "draft",
            "location_id": location_src.id,
            "location_dest_id": location_dest.id,
            "intercompany_parent_id": self.id,  # Keep track of the parent picking
        }
        return self.sudo().copy_data(default=vals)

    def _create_counterpart_pickings(self, mode):
        """Create counterpart pickings for all the pickings in the given mode"""
        counterparts = []
        for picking in self:
            counterpart = picking._create_counterpart_picking(mode)
            if counterpart:
                counterparts.append((picking, counterpart))
        return counterparts

    def _action_done(self):
        """
        Override to create the counterpart reception picking when the initial
        delivery picking is done.
        """
        counterparts = self._create_counterpart_pickings("in")

        rv = super(StockPicking, self)._action_done()

        for picking, counterpart in counterparts:
            picking._finalize_counterpart_picking(counterpart)

        return rv

    def action_confirm(self):
        """
        Override to create the counterpart delivery picking when the initial
        reception picking is confirmed.
        """
        # "out" counterpart pickings are created on manual confirm or when the
        # moves are assigned.

        rv = super(StockPicking, self).action_confirm()
        if not rv:
            return rv

        counterparts = self._create_counterpart_pickings("out")

        for picking, counterpart in counterparts:
            picking._finalize_counterpart_picking(counterpart)

        return rv

    def action_cancel(self):
        """
        Override to cancel counterpart pickings when the initial picking is
        cancelled.
        """
        rv = super(StockPicking, self).action_cancel()
        if not rv:
            return rv

        # Cancel counterpart pickings
        for picking in self:
            picking.intercompany_child_ids.action_cancel()

        return rv

    def _finalize_counterpart_picking(self, counterpart_picking):
        """
        Hook to finalize required steps on the counterpart picking after the initial
        outgoing picking is done.
        """
