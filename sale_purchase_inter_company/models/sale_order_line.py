# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# Copyright 2025 Batista10
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    intercompany_purchase_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        compute="_compute_intercompany_purchase_line_id",
        compute_sudo=True,
    )

    auto_purchase_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        string="Target Purchase Order Line",
        readonly=True,
        copy=False,
    )

    @api.model
    def _check_intercompany_product(self, dest_user, dest_company):
        if (
            self.product_id.company_id
            and self.product_id.company_id not in dest_user.company_ids
        ):
            raise UserError(
                _(
                    "You cannot create PO from SO because product '%s' "
                    "is not intercompany"
                )
                % self.product_id.name
            )

    @api.onchange("product_uom_qty")
    def _onchange_product_uom_qty_warn_intercompany(self):
        """Warn user that changing quantity in SO does not synchronize PO."""
        for line in self:
            # Only warn if it's an intercompany sale and there's a linked PO line
            if line.order_id.auto_purchase_order_id and line.auto_purchase_line_id:
                return {
                    "warning": {
                        "title": _("Warning"),
                        "message": _(
                            "Warning: changing the quantity here only updates "
                            "the Sale Order (SO) and not the Purchase Order (PO). "
                            "If you want the quantity to be updated "
                            "in both synchronized orders, make the change in the PO."
                        ),
                    }
                }

    @api.onchange("price_unit")
    def _onchange_price_unit_warn_intercompany(self):
        """Warns user that changing price in SO does not synchronize PO."""
        for line in self:
            # Only warn if it's an intercompany sale and there's a linked PO line
            if line.order_id.auto_purchase_order_id and line.auto_purchase_line_id:
                return {
                    "warning": {
                        "title": _("Warning"),
                        "message": _(
                            "Warning: changing the price here only updates "
                            "the Sale Order (SO) and not the Purchase Order (PO). "
                            "If you want the price to be updated "
                            "in both synchronized orders, make the change in the PO."
                        ),
                    }
                }

    @api.onchange("tax_id")
    def _onchange_tax_id_warn_intercompany(self):
        """Warns user that changing tax_id in SO does not synchronize PO."""
        for line in self:
            # Only warn if it's an intercompany sale and there's a linked PO line
            if line.order_id.auto_purchase_order_id and line.auto_purchase_line_id:
                return {
                    "warning": {
                        "title": _("Warning"),
                        "message": _(
                            "Warning: changing the taxes here only updates "
                            "the Sale Order (SO) and not the Purchase Order (PO). "
                            "If you want the taxes to be updated "
                            "in both synchronized orders, make the change in the PO."
                        ),
                    }
                }

    @api.onchange("product_id")
    def _onchange_product_added_warn_intercompany(self):
        """Warns when a new line is added to an intercompany SO.

        Does not warn if the change comes from a sync from the PO (_from_po_sync).
        """
        for line in self:
            # Ignore sections/notes
            if line.display_type in ("line_section", "line_note"):
                continue
            # SO intercompany and line NOT yet linked to PO
            if (
                line.order_id.auto_purchase_order_id
                and not line.auto_purchase_line_id
                and line.product_id
            ):
                return {
                    "warning": {
                        "title": _("Warning"),
                        "message": _(
                            "Warning: adding a product to an "
                            "intercompany Sale Order (SO).\n\n"
                            "Important: this line will NOT be created or updated "
                            "in the Purchase Order (PO).\n"
                            "If you want the line to exist and be synchronized "
                            "in both orders, add it to the PO."
                        ),
                    }
                }
