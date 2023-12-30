# Copyright (C) 2023 Cetmix OÜ
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockPickingIntercompanyBidirectional(models.Model):
    _inherit = "stock.picking"

    def _create_counterpart_picking(self):
        """Override of parent method to handle intercompany
        transactions depending on the operation types in the settings"""
        inter_company_partner = (
            self.env["res.company"]
            .sudo()
            .search([("partner_id", "=", self.partner_id.id)], limit=1)
        )

        if (
            self.env.company.intercompany_out_type_id.id == self.picking_type_id.id
            and inter_company_partner.intercompany_in_type_id
        ):
            return super()._create_counterpart_picking()
        else:
            return False

    @api.model
    def _check_company_consistency(self, company):
        """
        Override to set done qty or move packages depending on the company settings

        Args:
        - company (res.company): The intercompany instance.

        Returns:
        - move_ids: List of move IDs.
        - move_line_ids: Updated list of move line IDs.
        """
        move_ids, move_line_ids = super()._check_company_consistency(company)

        warehouse = company.intercompany_in_type_id.warehouse_id
        stock_move_line_obj = self.env["stock.move.line"]

        # Remove package-related data and update destination location
        # in move_ids and move_line_ids
        for move_data in move_ids:
            # Update destination location for each move
            move_data[2]["location_dest_id"] = warehouse.lot_stock_id.id
            # Set rule_id to False
            move_data[2]["rule_id"] = False
        for line_data in move_line_ids:
            # Prepare the move line ids
            line_data[2].update(
                {
                    "package_level_id": False,
                    "package_id": False,
                    "location_dest_id": warehouse.lot_stock_id.id,
                }
            )

        if company.auto_update_qty_done:
            # Update move_line_ids to include 'qty_done' based on counterpart move lines
            for line_data in move_line_ids:
                move_line = stock_move_line_obj.browse(
                    line_data[2]["counterpart_of_line_id"]
                )
                line_data[2]["qty_done"] = move_line.qty_done

        if self.env.company.move_packages and company.move_packages:
            # Unpack packages and clear package IDs from
            # the counterpart picking to manage the package movement
            if self.package_level_ids:
                packages = self.package_level_ids.mapped("package_id")
                packages.unpack()
            self.move_line_ids.write({"package_id": False, "result_package_id": False})
        else:
            # Clear result package ID from move_line_ids if conditions aren't met
            for line_data in move_line_ids:
                line_data[2].update({"result_package_id": False})

        if self.env.company.mirror_lot_numbers and company.mirror_lot_numbers:
            # Create assign lots/serial numbers with the same names
            # in the destination company automatically
            stock_lot_obj = self.env["stock.lot"].sudo()
            for line_data in move_line_ids:
                if "lot_id" in line_data[2] and line_data[2]["lot_id"]:
                    lot = stock_lot_obj.browse(line_data[2]["lot_id"])
                    new_lot = stock_lot_obj.with_company(company).create(
                        {
                            "name": lot.name,
                            "product_id": lot.product_id.id,
                            "company_id": company.id,
                        }
                    )
                    line_data[2].update(
                        {"lot_id": new_lot.id, "lot_name": new_lot.name}
                    )
        else:
            # Clear lots/SN numbers from move_line_ids if conditions aren't met
            for line_data in move_line_ids:
                line_data[2].update({"lot_id": False})

        return move_ids, move_line_ids

    def _get_counterpart_picking_vals(self, company):
        """
        Get counterpart picking values.
        Override to se the correct partner_id.

        Args:
        - company (res.company): The intercompany instance.

        Returns:
        - dict: Counterpart picking values.
        """
        result = super()._get_counterpart_picking_vals(company)
        result["partner_id"] = self.company_id.partner_id.id
        return result
