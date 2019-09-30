# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Quentin DUPONT (quentin.dupont@grap.coop)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestModule(TransactionCase):
    def setUp(self):
        super(TestModule, self).setUp()
        self.category_shop = self.env.ref("res_company_category.category_shop")
        self.category_shop_it = self.env.ref("res_company_category.category_shop_it")
        self.category_shop_organic_food = self.env.ref(
            "res_company_category.category_shop_organic_food"
        )

    # Test Section
    def test_01_has_right_parent(self):
        self.assertEqual(
            self.category_shop_it.parent_id,
            self.category_shop,
            "This category has not the right parent",
        )
        self.assertNotEqual(
            self.category_shop_it.parent_id,
            self.category_shop_organic_food,
            "This category has not the right parent",
        )
