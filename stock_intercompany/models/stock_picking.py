# Copyright 2021 Camptocamp
# Copyright 2022 Akretion (Florian Mounier <florian.mounier@akretion.com>)
# Copyright 2023 Cetmix OÜ
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    intercompany_parent_id = fields.Many2one(
        comodel_name="stock.picking",
        string="Intercompany Origin Picking",
        check_company=False,
        copy=False,
        help="Picking in another company that triggered the creation of this "
        "counterpart picking.",
    )
    intercompany_child_ids = fields.One2many(
        comodel_name="stock.picking",
        inverse_name="intercompany_parent_id",
        string="Intercompany Counterpart Pickings",
        help="Counterpart pickings created in other companies from this picking.",
    )
    has_counterpart = fields.Boolean(
        compute="_compute_has_counterpart",
        store=True,
        compute_sudo=True,
        help="True if this picking has at least one intercompany counterpart "
        "(parent or child).",
    )
    can_create_out_counterpart = fields.Boolean(
        compute="_compute_can_create_out_counterpart",
        help="Technical field: True when a delivery counterpart can be created "
        "from this reception (used to show the action button).",
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

    # -------------------------------------------------------------------------
    # Counterpart creation logic
    # -------------------------------------------------------------------------

    def _can_create_counterpart(self, mode):
        """Return the target company if a counterpart picking can be created
        for *self* in the given *mode* ('in' or 'out'), False otherwise.

        Mode 'in'  — triggered by a delivery (→ customer): create a reception.
        Mode 'out' — triggered by a reception (← supplier): create a delivery.
        """
        self.ensure_one()
        assert mode in ("in", "out"), f"Invalid mode: {mode}"

        if self.state == "cancel":
            return False
        # Skip if already linked to avoid loops and duplicates.
        if self.has_counterpart:
            return False

        # Check that the source location matches the expected usage for this mode.
        # Mode 'in': the picking goes *to* a customer location.
        # Mode 'out': the picking comes *from* a supplier location.
        check_location = self.location_dest_id if mode == "in" else self.location_id
        expected_usage = "customer" if mode == "in" else "supplier"
        if check_location.usage != expected_usage:
            return False

        company = (
            self.env["res.company"]
            .sudo()
            .search([("partner_id", "=", self.partner_id.id)], limit=1)
        )
        # Only create a counterpart toward a *different* company.
        if not company or company == self.company_id:
            return False

        # Respect the creation mode configured on the target company.
        if company.intercompany_picking_creation_mode not in (mode, "both"):
            return False

        if not self._check_intercompany_company(company, mode):
            return False

        return company

    def _check_intercompany_company(self, company, mode):
        """Hook allowing submodules to veto counterpart creation.

        Return False to prevent the counterpart from being created for *company*
        in the given *mode*.  Overriding this method should also update the
        domain returned by :meth:`_remaining_out_counterpart_picking_domain`
        accordingly so that the scheduled action stays consistent.
        """
        return True

    def _create_counterpart_picking(self, mode):
        """Create and confirm a counterpart picking for *self* in *mode*.

        Returns the newly created picking, or an empty recordset if no
        counterpart should be created.
        """
        self.ensure_one()

        company = self._can_create_counterpart(mode)
        if not company:
            return self.env["stock.picking"]

        intercompany_type = getattr(company, f"intercompany_{mode}_type_id")
        warehouse = intercompany_type.warehouse_id or (
            self.env["stock.warehouse"]
            .sudo()
            .search([("company_id", "=", company.id)], limit=1)
        )
        intercompany_type = intercompany_type or getattr(warehouse, f"{mode}_type_id")

        vals = self._prepare_counterpart_picking_vals(
            company, intercompany_type, warehouse, mode
        )
        picking = self.env["stock.picking"].sudo().create(vals)
        # Lock the origin picking to prevent modifications after counterpart creation.
        self.is_locked = True
        picking.action_confirm()
        return picking

    def _prepare_counterpart_picking_vals(
        self, company, intercompany_type, warehouse, mode
    ):
        """Return the values dict used to create the counterpart picking.

        Mode 'in'  (delivery → reception):
            source location : Suppliers (virtual, shared)
            dest   location : company stock
        Mode 'out' (reception → delivery):
            source location : company stock
            dest   location : Customers (virtual, shared)
        """
        supplier_location = self.env.ref("stock.stock_location_suppliers")
        customer_location = self.env.ref("stock.stock_location_customers")

        if mode == "in":
            location_src = supplier_location
            location_dest = (
                intercompany_type.default_location_dest_id or warehouse.lot_stock_id
            )
        else:
            location_src = warehouse.lot_stock_id
            location_dest = customer_location

        # Ensure the shared virtual locations are not restricted to a company.
        for loc in (supplier_location, customer_location):
            if loc.company_id:
                loc.sudo().company_id = False

        move_ids, move_line_ids = self._prepare_counterpart_move_vals(
            company, intercompany_type, location_src, location_dest
        )

        vals = {
            "partner_id": self.company_id.partner_id.id,
            "company_id": company.id,
            "origin": self.name,
            "picking_type_id": intercompany_type.id,
            "state": "draft",
            "location_id": location_src.id,
            "location_dest_id": location_dest.id,
            "intercompany_parent_id": self.id,
            "move_ids": move_ids,
            "move_line_ids": move_line_ids,
            "scheduled_date": self.scheduled_date,
            "priority": self.priority,
        }
        return vals

    def _prepare_counterpart_move_vals(
        self, company, intercompany_type, location_src, location_dest
    ):
        """Build the Command lists for moves and move lines of the counterpart."""
        supplier_location = self.env.ref("stock.stock_location_suppliers")

        common_move_vals = {
            "company_id": company.id,
            "location_id": location_src.id,
            "picking_type_id": intercompany_type.id,
        }
        common_line_vals = {
            "company_id": company.id,
            "location_id": supplier_location.id,
            "picking_type_id": intercompany_type.id,
        }

        move_ids = []
        for sm in self.move_ids.sudo():
            move_vals = sm.with_company(company).copy_data(
                dict(
                    common_move_vals,
                    intercompany_origin_move_id=sm.id,
                    picking_type_id=intercompany_type.id,
                )
            )[0]
            move_ids.append(Command.create(move_vals))

        move_line_ids = []
        for ln in self.move_line_ids.sudo():
            line_vals = ln.with_company(company).copy_data(
                dict(
                    common_line_vals,
                    intercompany_origin_line_id=ln.id,
                    lot_id=False,
                    lot_name=False,
                    move_id=False,
                    picking_type_id=intercompany_type.id,
                )
            )[0]
            move_line_ids.append(Command.create(line_vals))

        return move_ids, move_line_ids

    def _create_counterpart_pickings(self, mode):
        """Create counterpart pickings for all pickings in *self* for *mode*.

        Returns a list of (origin_picking, counterpart_picking) tuples for
        pickings where a counterpart was actually created.
        """
        counterparts = []
        for picking in self:
            counterpart = picking._create_counterpart_picking(mode)
            if counterpart:
                counterparts.append((picking, counterpart))
        return counterparts

    def _finalize_counterpart_picking(self, counterpart_picking):
        """Apply optional post-creation synchronisations to the counterpart.

        Submodules can extend this hook.  This base implementation handles:

        - **Sync Done Quantities** (``intercompany_sync_qty_done``): copy the
          ``quantity`` (done) from each origin move line to the corresponding
          counterpart move line, matched via ``intercompany_origin_line_id``.
        - **Share Lots / Serial Numbers** (``intercompany_share_lot``): remove
          ``company_id`` from lots used on the origin picking so they become
          visible in all companies, then assign them to the matching counterpart
          move lines.
        """
        if not counterpart_picking:
            return
        dest_company = counterpart_picking.sudo().company_id
        sync_qty = dest_company.intercompany_sync_qty_done
        share_lot = dest_company.intercompany_share_lot
        if not sync_qty and not share_lot:
            return

        for cp_line in counterpart_picking.sudo().move_line_ids:
            origin_line = cp_line.intercompany_origin_line_id
            if not origin_line:
                continue
            vals = {}
            if sync_qty:
                vals["quantity"] = origin_line.quantity
            if share_lot and origin_line.lot_id:
                vals["lot_id"] = self._share_lot(origin_line.lot_id).id
            if vals:
                cp_line.write(vals)

    def _share_lot(self, lot):
        """Make *lot* company-independent so it is visible across all companies.

        Sets ``company_id`` to ``False`` on the lot (requires sudo).  The
        PostgreSQL UNIQUE constraint on ``(name, product_id, company_id)``
        treats NULL values as distinct, so a single shared lot with
        ``company_id=False`` does not conflict with company-specific lots
        having the same name and product.

        Returns the lot record (unchanged reference, modified in place).
        """
        lot = lot.sudo()
        if lot.company_id:
            lot.company_id = False
        return lot

    # -------------------------------------------------------------------------
    # Overrides of standard stock actions
    # -------------------------------------------------------------------------

    def _action_done(self):
        """Create 'in' counterpart pickings before marking the delivery as done."""
        counterparts = self._create_counterpart_pickings("in")
        res = super()._action_done()
        for picking, counterpart in counterparts:
            picking._finalize_counterpart_picking(counterpart)
        return res

    def action_create_counterpart(self):
        """Manually create 'out' counterpart pickings from reception pickings.

        This action is triggered by the 'Create Counterpart' button shown on
        reception pickings whose partner is an inter-company partner configured
        with 'Delivery Only' or 'Create Both' mode.
        """
        counterparts = self._create_counterpart_pickings("out")
        for picking, counterpart in counterparts:
            picking._finalize_counterpart_picking(counterpart)
        return True

    def action_cancel(self):
        """Also cancel intercompany child pickings when cancelling a picking."""
        res = super().action_cancel()
        if not res:
            return res
        self.invalidate_recordset()
        for picking in self.sudo():
            picking.intercompany_child_ids.action_cancel()
        return res

    def action_toggle_is_locked(self):
        """Prevent unlocking a picking that has intercompany counterparts."""
        self.invalidate_recordset()
        if self.is_locked and self.has_counterpart:
            raise UserError(
                _("You cannot unlock a picking that has an intercompany counterpart.")
            )
        return super().action_toggle_is_locked()

    # -------------------------------------------------------------------------
    # Scheduled action / remaining counterparts
    # -------------------------------------------------------------------------

    def _remaining_out_counterpart_picking_domain(self, companies):
        """Return the domain of reception pickings that still need a delivery
        counterpart to be created (used by the scheduled action).

        *companies* is the recordset of companies that have 'out' or 'both'
        creation mode configured.
        """
        return [
            ("state", "not in", ("cancel", "done")),
            ("partner_id", "in", companies.mapped("partner_id").ids),
            ("has_counterpart", "=", False),
            ("location_id.usage", "=", "supplier"),
        ]

    def _remaining_out_counterpart_picking(self):
        """Return reception pickings that still need a delivery counterpart."""
        companies = (
            self.env["res.company"]
            .sudo()
            .search(
                [
                    (
                        "intercompany_picking_creation_mode",
                        "in",
                        ("out", "both"),
                    )
                ]
            )
        )
        return (
            self.env["stock.picking"]
            .sudo()
            .search(self._remaining_out_counterpart_picking_domain(companies))
        )

    def _create_remaining_out_counterpart(self):
        """Scheduled action: create delivery counterparts for all eligible
        reception pickings that do not yet have one."""
        self._remaining_out_counterpart_picking()._create_counterpart_pickings("out")
