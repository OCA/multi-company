from odoo import _, api, fields, models
from odoo.exceptions import UserError


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

    has_counterpart = fields.Boolean(
        compute="_compute_has_counterpart",
        store=True,
        compute_sudo=True,
    )

    can_create_out_counterpart = fields.Boolean(
        string="Technical field to check if a outgoing counterpart can be created",
        compute="_compute_can_create_out_counterpart",
        store=False,
    )

    @api.depends("intercompany_parent_id", "intercompany_child_ids")
    def _compute_has_counterpart(self):
        for picking in self:
            picking.has_counterpart = bool(
                picking.intercompany_parent_id or picking.intercompany_child_ids
            )

    @api.depends(
        "company_id",
        "partner_id",
        "location_id",
        "location_dest_id",
        "intercompany_parent_id",
        "intercompany_child_ids",
    )
    def _compute_can_create_out_counterpart(self):
        for picking in self:
            picking.can_create_out_counterpart = bool(
                picking._can_create_counterpart("out")
            )

    def _can_create_counterpart(self, mode):
        """
        Check if the picking can create a counterpart picking.
        Returns the company to use for the counterpart picking if it can be created.
        """
        self.ensure_one()
        assert mode in ["in", "out"], "Invalid mode: %s" % mode
        if self.state == "cancel":
            return

        # Skip if already has a parent to avoid looping
        # Also skip if already has children to avoid creating a duplicate
        if self.has_counterpart:
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

        return company

    def _create_counterpart_picking(self, mode):
        """
        Create a counterpart picking for the given picking in the given mode:
        Mode in: Create incoming from outgoing picking
        Mode out: Create outgoing from incoming picking
        """

        self.ensure_one()
        if self.state == "cancel":
            return

        company = self._can_create_counterpart(mode)
        if not company:
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
        self.is_locked = True
        picking.action_confirm()
        return picking

    def _check_intercompany_company(self, company, mode):
        """
        Hook to check if the given company is valid for the given mode.
        If you override this method, please update the domain
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
        result = self.sudo().copy_data(default=vals)
        for picking in result:
            for move_line in picking["move_lines"]:
                del move_line[2]["rule_id"]
                del move_line[2]["orderpoint_id"]
        return result

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

    def action_create_counterpart(self):
        """
        New action to validate the reception picking and create the counterpart
        """
        # "out" counterpart pickings are created on manual action.
        counterparts = self._create_counterpart_pickings("out")

        for picking, counterpart in counterparts:
            picking._finalize_counterpart_picking(counterpart)

        return True

    def action_cancel(self):
        """
        Override to cancel counterpart pickings when the initial picking is
        cancelled.
        """
        rv = super(StockPicking, self).action_cancel()
        if not rv:
            return rv

        # Cancel counterpart pickings
        # We need to invalidate the cache to get the sudo value for
        # intercompany_child_ids
        self.invalidate_cache()
        for picking in self.sudo():
            picking.intercompany_child_ids.action_cancel()

        return rv

    def _finalize_counterpart_picking(self, counterpart_picking):
        """
        Hook to finalize required steps on the counterpart picking after the initial
        outgoing picking is done.
        """

    def action_toggle_is_locked(self):
        """
        Override to prevent unlocking pickings that have a counterpart
        """
        self.invalidate_cache()
        if self.is_locked and self.has_counterpart:
            raise UserError(_("You cannot unlock a picking that has a counterpart."))
        return super(StockPicking, self).action_toggle_is_locked()

    def _remaining_out_counterpart_picking_domain(self, companies):
        """
        Hook returning the domain of the pickings that need to create a outgoing
        counterpart picking.
        """
        return [
            ("state", "!=", "cancel"),
            (
                "partner_id",
                "in",
                companies.mapped("partner_id").ids,
            ),
            ("has_counterpart", "=", False),
            ("location_id.usage", "=", "supplier"),
        ]

    def _remaining_out_counterpart_picking(self):
        """
        Return the pickings that need to create a outgoing counterpart picking.
        """

        companies_with_out_creation = (
            self.env["res.company"]
            .sudo()
            .search([("intercompany_picking_creation_mode", "in", ["out", "both"])])
        )
        return (
            self.env["stock.picking"]
            .sudo()
            .search(
                self._remaining_out_counterpart_picking_domain(
                    companies_with_out_creation
                )
            )
        )

    def _create_remaining_out_counterpart(self):
        """
        Create the remaining counterpart pickings for the pickings that have not
        been created yet.
        """
        self._remaining_out_counterpart_picking()._create_counterpart_pickings("out")
