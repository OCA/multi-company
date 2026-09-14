#  Copyright (c) Akretion 2021
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from odoo.tests import TransactionCase


class TestPurchaseQuickIntercompany(TransactionCase):
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

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.company_x = cls.env["res.company"].create({"name": "x Company"})
        cls.partner_x = cls.company_x.partner_id
        cls.user_x = cls.env["res.users"].create(
            {
                "name": "x user",
                "company_ids": [cls.company_x.id],
                "company_id": cls.company_x.id,
                "login": "x",
            }
        )
        cls.warehouse_x = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company_x.id)]
        )
        cls.location_x = cls.warehouse_x.lot_stock_id

        cls.company_y = cls.env["res.company"].create({"name": "y Company"})
        cls.partner_y = cls.company_y.partner_id
        cls.user_y = cls.env["res.users"].create(
            {
                "name": "y user",
                "company_ids": [cls.company_y.id],
                "company_id": cls.company_y.id,
                "login": "y",
            }
        )
        cls.warehouse_y = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company_y.id)]
        )
        cls.location_y = cls.warehouse_y.lot_stock_id

        cls.partner_other = cls.env.ref("base.res_partner_12")
        cls.product = cls.env.ref("product.product_product_8")

    def test_quick_intercompany_stock_level(self):
        """
        Simplest scenario (x->y):
        set stock levels for company y,
        user from company x tries to check company y's stock levels
        using purchase_quick's interface
        """
        self._set_y_stock_to(47.0)
        po = self.env["purchase.order"].create({"partner_id": self.partner_y.id})
        product = self.product.with_user(self.user_x).with_context(
            **{
                "parent_model": "purchase.order",
                "parent_id": po.id,
                "show_intercompany_qty": True,
            }
        )
        self.assertAlmostEqual(float(product.quick_intercompany_stock_level), 47.0)

    def test_quick_intercompany_stock_level_2(self):
        """
        Same as previous test, but check both ways (x->y and y->x)
        """
        self._set_y_stock_to(47.0)
        self._set_x_stock_to(61.0)

        po_y = self.env["purchase.order"].create({"partner_id": self.partner_y.id})
        product = self.product.with_user(self.user_x).with_context(
            **{
                "parent_model": "purchase.order",
                "parent_id": po_y.id,
                "show_intercompany_qty": True,
            }
        )
        self.assertAlmostEqual(float(product.quick_intercompany_stock_level), 47.0)

        po_x = self.env["purchase.order"].create({"partner_id": self.partner_x.id})
        product = self.product.with_user(self.user_y).with_context(
            **{
                "parent_model": "purchase.order",
                "parent_id": po_x.id,
                "show_intercompany_qty": True,
            }
        )
        self.assertAlmostEqual(float(product.quick_intercompany_stock_level), 61.0)

    def test_quick_intercompany_stock_level_change_uom(self):
        """
        Changing UoM on the fly -> we should get updated stock levels
        """
        self._set_y_stock_to(47.0)
        po = self.env["purchase.order"].create({"partner_id": self.partner_y.id})
        self.product.quick_uom_id = self.env.ref("uom.product_uom_dozen")
        product = self.product.with_user(self.user_x).with_context(
            **{
                "parent_model": "purchase.order",
                "parent_id": po.id,
                "show_intercompany_qty": True,
            }
        )
        self.assertAlmostEqual(
            float(product.quick_intercompany_stock_level), 3.92
        )  # 47/12 ~=3.916

    def test_quick_stock_no_company(self):
        """
        Selecting a seller with no company should display N/A
        """
        self._set_y_stock_to(47.0)
        self._set_x_stock_to(61.0)
        po = self.env["purchase.order"].create({"partner_id": self.partner_other.id})
        product = self.product.with_user(self.user_y).with_context(
            **{
                "parent_model": "purchase.order",
                "parent_id": po.id,
                "show_intercompany_qty": True,
            }
        )
        self.assertEqual(product.quick_intercompany_stock_level, 0.0)

    def test_search_quick_intercompany_stock_level(self):
        self._set_y_stock_to(47.0)
        self._set_x_stock_to(33.0)
        po = self.env["purchase.order"].create({"partner_id": self.partner_y.id})

        product = self.product.with_user(self.user_x).with_context(
            **{
                "parent_model": "purchase.order",
                "parent_id": po.id,
                "show_intercompany_qty": True,
            }
        )
        search_result = product._search_quick_intercompany_stock_level("!=", 0.0)
        self.assertTrue(len(search_result), 1)
        self.assertIn(product.id, search_result[0][2])
