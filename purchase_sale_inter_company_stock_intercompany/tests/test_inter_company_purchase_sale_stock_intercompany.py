from odoo.addons.purchase_sale_inter_company.tests.common import (
    TestPurchaseSaleInterCompanyCommon,
)
from odoo.addons.stock_intercompany.tests.common import TestStockIntercompanyCommon


class TestInterCompanyPurchaseSaleStockIntercompany(
    TestStockIntercompanyCommon, TestPurchaseSaleInterCompanyCommon
):
    def test_sync_picking_avoid_duplicate_in(self):
        self.company_a.intercompany_picking_creation_mode = "both"
        self.company_b.intercompany_picking_creation_mode = "both"

        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        sale = self._approve_po(purchase)

        self.assertEqual(len(purchase.picking_ids), 1)
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertFalse(purchase.picking_ids.intercompany_parent_id)
        self.assertFalse(purchase.picking_ids.intercompany_child_ids)
        self.assertFalse(sale.picking_ids.intercompany_parent_id)
        self.assertFalse(sale.picking_ids.intercompany_child_ids)

    def test_sync_picking_avoid_duplicate_out(self):
        self.company_a.intercompany_picking_creation_mode = "both"
        self.company_b.intercompany_picking_creation_mode = "both"

        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        sale = self._approve_po(purchase)

        self.assertEqual(len(purchase.picking_ids), 1)
        self.assertEqual(len(sale.picking_ids), 1)
        sale.picking_ids.move_lines.quantity_done = (
            sale.picking_ids.move_lines.product_qty
        )

        sale.picking_ids.sudo().action_confirm()
        sale.picking_ids.sudo().button_validate()
        self.assertEqual(len(sale.picking_ids), 1)

        self.assertFalse(purchase.picking_ids.intercompany_parent_id)
        self.assertFalse(purchase.picking_ids.intercompany_child_ids)
        self.assertFalse(sale.picking_ids.intercompany_parent_id)
        self.assertFalse(sale.picking_ids.intercompany_child_ids)

    def test_remaining_out_counterpart_filter_with_purchase_created_counterpart(self):
        self.company2.intercompany_picking_creation_mode = "out"
        self.assertEqual(
            len(self.env["stock.picking"]._remaining_out_counterpart_picking()), 0
        )

        # Create pickings from po/so
        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        self._approve_po(purchase)

        self.assertEqual(
            len(self.env["stock.picking"]._remaining_out_counterpart_picking()), 0
        )
