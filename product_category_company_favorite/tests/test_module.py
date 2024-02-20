# Copyright (C) 2023-Today: GRAP (<http://www.grap.coop/>)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import Form, common


class TestModule(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.main_company = self.env.ref("base.main_company")
        self.demo_company = self.env.ref(
            "product_category_company_favorite.demo_company"
        )

        self.ProductCategory = self.env["product.category"]
        self.ResCompany = self.env["res.company"]

        self.category_A = self.env.ref("product.product_category_all")
        self.category_A_2 = self.env.ref("product.product_category_1")
        self.category_A_2_x = self.env.ref("product.product_category_5")

    def _change_company(self, item, company=False):
        if not company:
            company = self.demo_company
        return item.with_company(company)

    def test_00_hook(self):
        self.assertTrue(self.category_A.is_favorite)
        self.assertTrue(self._change_company(self.category_A).is_favorite)

    def test_10_write_value_company_dependant(self):
        self.category_A.is_favorite = False
        self.assertFalse(self.category_A.is_favorite)
        self.assertTrue(self._change_company(self.category_A).is_favorite)

    def test_11_write_value_recursive(self):
        self.category_A.is_favorite = False
        self.assertFalse(self.category_A.is_favorite)
        self.assertFalse(self.category_A_2.is_favorite)
        self.assertFalse(self.category_A_2_x.is_favorite)

    def test_20_create_new_category_not_favorite(self):
        new_root_categ = self.ProductCategory.create(
            {
                "name": "New Root Category",
                "is_favorite": False,
            }
        )
        self.assertFalse(new_root_categ.is_favorite)
        self.assertFalse(self._change_company(new_root_categ).is_favorite)

        new_child_categ = self.ProductCategory.create(
            {
                "name": "New Child Category",
                "parent_id": new_root_categ.id,
            }
        )
        self.assertFalse(new_child_categ.is_favorite)
        self.assertFalse(self._change_company(new_child_categ).is_favorite)

    def test_21_create_new_category_favorite(self):
        new_root_categ = self.ProductCategory.create(
            {
                "name": "New Root Category",
                "is_favorite": True,
            }
        )
        self.assertTrue(new_root_categ.is_favorite)
        self.assertTrue(self._change_company(new_root_categ).is_favorite)

        new_child_categ = self.ProductCategory.create(
            {
                "name": "New Child Category",
                "parent_id": new_root_categ.id,
            }
        )
        self.assertTrue(self._change_company(new_child_categ).is_favorite)

    def test_30_create_new_company(self):
        company_vals = {
            "name": "New Company",
        }
        new_company = self.ResCompany.create(company_vals)

        self.assertTrue(
            self._change_company(self.category_A, company=new_company).is_favorite
        )
        self.assertTrue(
            self._change_company(self.category_A_2_x, company=new_company).is_favorite
        )

    def test_40_name_search(self):
        self.category_A_2_x.is_favorite = True
        self.assertTrue(self.ProductCategory.name_search(self.category_A_2_x.name))

        self.category_A_2_x.is_favorite = False
        self.assertFalse(self.ProductCategory.name_search(self.category_A_2_x.name))

    def test_40_test_onchange(self):
        root_categ_favorite = self.ProductCategory.create(
            {
                "name": "New Root Category 1",
                "is_favorite": True,
            }
        )
        root_categ_not_favorite = self.ProductCategory.create(
            {
                "name": "New Root Category 2",
                "is_favorite": False,
            }
        )
        categ = Form(self.env["product.category"])
        self.assertFalse(categ.is_favorite)
        categ.parent_id = root_categ_favorite
        self.assertTrue(categ.is_favorite)
        categ.parent_id = root_categ_not_favorite
        self.assertFalse(categ.is_favorite)
