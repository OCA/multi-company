# Copyright 2026 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import TransactionCase

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class TestPurchaseOrderLineDisplaySupplierStock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.main_company = cls.env.ref("base.main_company")
        cls.vendor_company = cls.env["res.company"].create({"name": "Vendor Co"})
        cls.vendor_warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.vendor_company.id)], limit=1
        )
        cls.vendor_warehouse.display_stock_on_sol = True
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "is_storable": True,
            }
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product,
            cls.vendor_warehouse.lot_stock_id,
            30,
        )
        cls.purchase_order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.vendor_company.partner_id.id,
                "company_id": cls.main_company.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "name": "Test Product",
                            "product_qty": 1,
                            "product_uom": cls.product.uom_id.id,
                            "date_planned": fields.Datetime.now(),
                            "price_unit": 10,
                        },
                    )
                ],
            }
        )
        cls.line = cls.purchase_order.order_line

    def _create_incoming_move(self, name, date, qty=5):
        return self.env["stock.move"].create(
            {
                "name": name,
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": qty,
                "location_id": self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": self.vendor_warehouse.lot_stock_id.id,
                "company_id": self.vendor_company.id,
                "date": date,
            }
        )

    def test_supplier_stock_from_intercompany_supplier(self):
        self.assertIn("30.0", self.line.supplier_stock_info)

    def test_supplier_stock_summed_over_warehouses(self):
        warehouse_2 = self.env["stock.warehouse"].create(
            {
                "name": "Vendor WH2",
                "code": "VWH2",
                "company_id": self.vendor_company.id,
                "display_stock_on_sol": True,
            }
        )
        self.env["stock.quant"]._update_available_quantity(
            self.product,
            warehouse_2.lot_stock_id,
            12,
        )
        self.assertIn("42.0", self.line.supplier_stock_info)

    def test_no_info_when_supplier_not_a_company(self):
        self.purchase_order.partner_id = self.env.ref("base.res_partner_2")
        self.assertFalse(self.line.supplier_stock_info)

    def test_replenishment_date_shown_when_no_stock(self):
        self.env["stock.quant"]._update_available_quantity(
            self.product,
            self.vendor_warehouse.lot_stock_id,
            quantity=-30,
        )
        move_late = self._create_incoming_move("R1", "2026-10-10 08:00:00")
        move_early = self._create_incoming_move("R2", "2026-09-01 08:00:00")
        (move_late | move_early).sudo()._action_confirm()
        self.line.invalidate_recordset(fnames=["supplier_stock_info"])
        self.assertIn("Replenishment: 2026-09-01", self.line.supplier_stock_info)

    def test_stock_takes_precedence_over_replenishment_date(self):
        move = self._create_incoming_move("Incoming", "2026-09-01 08:00:00")
        move.sudo()._action_confirm()
        self.line.invalidate_recordset(fnames=["supplier_stock_info"])
        self.assertIn("30.0", self.line.supplier_stock_info)
        self.assertNotIn("Replenishment", self.line.supplier_stock_info)
