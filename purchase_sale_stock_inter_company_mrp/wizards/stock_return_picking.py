# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import Command, models

from ..models.stock_picking import KIT_QUANTITIES_FILTERS


class ReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def _create_intercompany_return_wizard(self, new_picking):
        """Handle kits when returning an intercompany delivery picking (sale side).

        The base implementation matches the purchase return lines to the sale
        return lines by product, which is wrong for kits: the sale and
        purchase sides may have different BOMs and move structures (see
        ``StockPicking._set_intercompany_kit_quantities_done``).

        Recompute the returned kit quantity from the sale return moves, then
        explode it through the purchase BOM so that each purchase return line
        gets its own quantity.
        """
        po_reception_picking = self.picking_id.intercompany_picking_id
        has_kit, qty_by_bom_line, qty_by_product = self._get_purchase_return_quantities(
            new_picking, po_reception_picking.sudo()
        )
        if not has_kit:
            return super()._create_intercompany_return_wizard(new_picking)

        po_company = po_reception_picking.sudo().company_id
        intercompany_user = po_company.intercompany_sale_user_id
        vals = {"picking_id": po_reception_picking.id}
        return_wizard = (
            self.env["stock.return.picking"]
            .with_context(active_id=po_reception_picking.id)
            .with_user(intercompany_user)
            .with_company(po_company)
            .create(vals)
        )
        # Drop the return lines whose purchase line is not part of the sale
        # return.
        purchase_lines = new_picking.move_ids.sale_line_id.auto_purchase_line_id
        exclude_moves = return_wizard.product_return_moves.filtered(
            lambda line: line.move_id.purchase_line_id not in purchase_lines
        )
        return_wizard.product_return_moves = [
            Command.unlink(prm.id) for prm in exclude_moves
        ]
        # The return lines must match the quantities exploded from the BOM
        # of the receipt, otherwise the BOM changed since the receipt.
        return_moves = return_wizard.product_return_moves.move_id
        for purchase_line, line_qty_by_bom_line in qty_by_bom_line.items():
            return_moves.filtered(
                lambda m, pl=purchase_line: m.purchase_line_id == pl
            )._check_intercompany_kit_bom_changed(line_qty_by_bom_line)
        # Check if the kit products actually returned are tracked by lot
        kit_return_lines = return_wizard.product_return_moves.filtered(
            lambda line: line.move_id.bom_line_id
            in qty_by_bom_line.get(line.move_id.purchase_line_id, {})
            or self.picking_id._get_intercompany_kit_bom(
                line.product_id, self.picking_id.company_id
            )
        )
        kit_return_lines.move_id._check_intercompany_kit_tracking()
        for po_return_line in return_wizard.product_return_moves:
            purchase_line = po_return_line.move_id.purchase_line_id
            bom_line = po_return_line.move_id.bom_line_id
            if bom_line:
                quantity = qty_by_bom_line[purchase_line][bom_line]
            else:
                quantity = qty_by_product[purchase_line]
            po_return_line.write({"quantity": quantity})
        return return_wizard

    def _get_purchase_return_quantities(self, so_return_picking, po_reception_picking):
        """Return the quantities to set on the purchase return lines.

        Return a ``(has_kit, qty_by_bom_line, qty_by_product)`` tuple, the
        quantities being expressed in the purchased product UoM.

        Both are keyed by purchase line, as the same product may be ordered
        on several lines. ``qty_by_bom_line`` maps each purchase line to the
        quantities of the kit components by BOM line when the purchase side
        has a BOM, so each component move gets the quantity of its own BOM
        line (important when the same product is used on several lines).
        ``qty_by_product`` maps the purchase line to the quantity of the kit
        product when the purchase side has no BOM, or of the plain products
        of a mixed return.
        """
        qty_by_bom_line = defaultdict(lambda: defaultdict(float))
        qty_by_product = defaultdict(float)
        has_kit = False
        for sale_line, sale_return_moves in so_return_picking.move_ids.grouped(
            "sale_line_id"
        ).items():
            if not sale_line:
                continue
            purchase_line = sale_line.auto_purchase_line_id
            sale_bom = self.picking_id._get_intercompany_kit_bom(
                sale_line.product_id, sale_line.company_id
            )
            purchase_bom = po_reception_picking._get_intercompany_kit_bom(
                sale_line.product_id, po_reception_picking.company_id
            )
            if not purchase_bom:
                po_reception_picking.move_ids.filtered(
                    lambda m, pl=purchase_line: m.purchase_line_id == pl
                )._check_intercompany_kit_bom_changed({})
            if not sale_bom and not purchase_bom:
                # Plain product, not related to a kit: keep the returned
                # quantity as is.
                qty_by_product[purchase_line] += sum(
                    sale_return_moves.mapped("product_qty")
                )
                continue
            has_kit = True
            sale_return_moves._check_intercompany_kit_tracking()
            if sale_bom:
                # 'sale-kit' or 'sale-purchase-kit': the sale side returns
                # kit components, recompute the returned kit quantity from
                # their quantities.
                kit_qty_sold = sale_line.product_uom._compute_quantity(
                    sale_line.product_uom_qty, sale_bom.product_uom_id
                )
                kit_qty_returned = sale_return_moves._compute_kit_quantities(
                    sale_line.product_id, kit_qty_sold, sale_bom, KIT_QUANTITIES_FILTERS
                )
                qty_returned = sale_bom.product_uom_id._compute_quantity(
                    kit_qty_returned, sale_line.product_id.uom_id
                )
            else:
                # 'purchase-kit': the sale side returns the kit product.
                qty_returned = sum(sale_return_moves.mapped("product_qty"))
            if purchase_bom:
                # 'purchase-kit' or 'sale-purchase-kit': the purchase side
                # receives kit components, explode the received BOM.
                purchase_qty = sale_line.product_id.uom_id._compute_quantity(
                    qty_returned, purchase_bom.product_uom_id
                )
                __, purchase_bom_lines = purchase_bom.explode(
                    sale_line.product_id, purchase_qty / purchase_bom.product_qty
                )
                for bom_line, bom_line_data in purchase_bom_lines:
                    qty_by_bom_line[purchase_line][bom_line] += (
                        bom_line.product_uom_id._compute_quantity(
                            bom_line_data["qty"], bom_line.product_id.uom_id
                        )
                    )
            else:
                # 'sale-kit': the purchase side receives the kit product
                # (no purchase BOM).
                qty_by_product[purchase_line] += qty_returned
        return has_kit, qty_by_bom_line, qty_by_product
