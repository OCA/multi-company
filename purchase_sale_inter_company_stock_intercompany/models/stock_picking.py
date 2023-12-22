from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _check_intercompany_company(self, company, mode):
        """
        Avoid creating a counterpart picking if this picking is issued from a
        purchase order and so_from_po is set to True on the target company
        because the counterpart picking will be created by the sale order.
        """
        if mode == "out" and self.purchase_id and company.so_from_po:
            return False
        return super()._check_intercompany_company(company, mode)

    def _create_counterpart_picking(self, mode):
        # Skip linked pickings from purchase sale inter company
        if self.intercompany_picking_id:
            return

        return super()._create_counterpart_picking(mode)

    def _remaining_out_counterpart_picking_domain(self, companies):
        """
        Override to filter out picking issued from a purchase order on companies
        that have so_from_po set to True.
        """
        so_from_po_companies = companies.filtered("so_from_po")
        domain = super()._remaining_out_counterpart_picking_domain(companies)
        domain += [
            "|",
            ("purchase_id", "=", False),
            ("partner_id", "not in", so_from_po_companies.mapped("partner_id").ids),
        ]

        return domain
