#  Copyright (c) Akretion 2021
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from odoo.tests import SavepointCase


class TestPurchaseQuickIntercompany(SavepointCase):
    def _set_x_stock_to(self, qty):
        self._set_stock_to(self.company_x.id, self.location_x.id, qty)

    def _set_y_stock_to(self, qty):
        self._set_stock_to(self.company_y.id, self.location_y.id, qty)

    def _set_stock_to(self, company_id, location_id, qty):
        inventory = self.env["stock.inventory"].create(
            {
                "location_ids": [location_id],
                "name": "Test starting inventory",
                "company_id": company_id,
            }
        )
        self.env["stock.inventory.line"].create(
            {
                "inventory_id": inventory.id,
                "location_id": location_id,
                "product_id": self.product.id,
                "product_uom_id": self.product.uom_id.id,
                "product_qty": qty,
            }
        )
        inventory.action_start()
        inventory.action_validate()

    def setUp(self):
        super().setUp()

        self.company_x = self.env["res.company"].create({"name": "x Company"})
        self.partner_x = self.company_x.partner_id
        self.user_x = self.env["res.users"].create(
            {
                "name": "x user",
                "company_ids": [self.company_x.id],
                "company_id": self.company_x.id,
                "login": "x",
            }
        )
        self.warehouse_x = self.env["stock.warehouse"].search(
            [("company_id", "=", self.company_x.id)]
        )
        self.location_x = self.warehouse_x.lot_stock_id

        self.company_y = self.env["res.company"].create({"name": "y Company"})
        self.partner_y = self.company_y.partner_id
        self.user_y = self.env["res.users"].create(
            {
                "name": "y user",
                "company_ids": [self.company_y.id],
                "company_id": self.company_y.id,
                "login": "y",
            }
        )
        self.warehouse_y = self.env["stock.warehouse"].search(
            [("company_id", "=", self.company_y.id)]
        )
        self.location_y = self.warehouse_y.lot_stock_id

        self.partner_other = self.env.ref("base.res_partner_12")
        self.product = self.env.ref("product.product_product_8")

    def test_quick_stock_level(self):
        """
        Simplest scenario (x->y):
        set stock levels for company y,
        user from company x tries to check company y's stock levels
        using purchase_quick's interface
        """
        self._set_y_stock_to(47.0)
        po = self.env["purchase.order"].create({"partner_id": self.partner_y.id})
        product = self.product.with_user(self.user_x).with_context(
            {"parent_model": "purchase.order", "parent_id": po.id}
        )
        self.assertAlmostEqual(float(product.quick_stock_level), 47.0)

    def test_quick_stock_level_2(self):
        """
        Same as previous test, but check both ways (x->y and y->x)
        """
        self._set_y_stock_to(47.0)
        self._set_x_stock_to(61.0)

        po_y = self.env["purchase.order"].create({"partner_id": self.partner_y.id})
        product = self.product.with_user(self.user_x).with_context(
            {"parent_model": "purchase.order", "parent_id": po_y.id}
        )
        self.assertAlmostEqual(float(product.quick_stock_level), 47.0)

        po_x = self.env["purchase.order"].create({"partner_id": self.partner_x.id})
        product = self.product.with_user(self.user_y).with_context(
            {"parent_model": "purchase.order", "parent_id": po_x.id}
        )
        self.assertAlmostEqual(float(product.quick_stock_level), 61.0)

    def test_quick_stock_level_change_uom(self):
        """
        Changing UoM on the fly -> we should get updated stock levels
        """
        self._set_y_stock_to(47.0)
        po = self.env["purchase.order"].create({"partner_id": self.partner_y.id})
        self.product.quick_uom_id = self.env.ref("uom.product_uom_dozen")
        product = self.product.with_user(self.user_x).with_context(
            {"parent_model": "purchase.order", "parent_id": po.id}
        )
        self.assertAlmostEqual(float(product.quick_stock_level), 3.92)  # 47/12 ~=3.916

    def test_quick_stock_no_company(self):
        """
        Selecting a seller with no company should display N/A
        """
        self._set_y_stock_to(47.0)
        self._set_x_stock_to(61.0)
        po = self.env["purchase.order"].create({"partner_id": self.partner_other.id})
        product = self.product.with_user(self.user_y).with_context(
            {"parent_model": "purchase.order", "parent_id": po.id}
        )
        self.assertEqual(product.quick_stock_level, "N/A")
