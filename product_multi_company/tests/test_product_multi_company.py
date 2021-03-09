# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import AccessError
from odoo.tests import common


class TestProductMultiCompany(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        groups = cls.env.ref("base.group_system")
        cls.product_obj = cls.env["product.product"]
        cls.company_obj = cls.env["res.company"]
        cls.company_1 = cls.company_obj.create({"name": "Test company 1"})
        cls.company_2 = cls.company_obj.create({"name": "Test company 2"})
        cls.product_company_none = cls.product_obj.create(
            {
                "name": "Product without company",
                "company_ids": [(6, 0, [])],
                "company_id": False,
            }
        )
        cls.product_company_1 = cls.product_obj.create(
            {
                "name": "Product from company 1",
                "company_ids": [(6, 0, cls.company_1.ids)],
            }
        )
        cls.product_company_2 = cls.product_obj.create(
            {
                "name": "Product from company 2",
                "company_ids": [(6, 0, cls.company_2.ids)],
            }
        )
        cls.product_company_both = cls.product_obj.create(
            {
                "name": "Product for both companies",
                "company_ids": [(6, 0, (cls.company_1 + cls.company_2).ids)],
            }
        )
        cls.user_company_1 = cls.env["res.users"].create(
            {
                "name": "User company 1",
                "login": "user_company_1",
                "groups_id": [(6, 0, groups.ids)],
                "company_id": cls.company_1.id,
                "company_ids": [(6, 0, cls.company_1.ids)],
            }
        )
        cls.user_company_2 = cls.env["res.users"].create(
            {
                "name": "User company 2",
                "login": "user_company_2",
                "groups_id": [(6, 0, groups.ids)],
                "company_id": cls.company_2.id,
                "company_ids": [(6, 0, cls.company_2.ids)],
            }
        )

    def test_create_product(self):
        product = self.env["product.product"].create({"name": "Test"})
        company = self.env.company
        self.assertTrue(company.id in product.company_ids.ids)

    def test_company_none(self):
        self.assertFalse(self.product_company_none.company_id)
        # All of this should be allowed
        self.product_company_none.with_user(
            self.user_company_1.id
        ).description_sale = "Test 1"
        self.product_company_none.with_user(
            self.user_company_2.id
        ).description_sale = "Test 2"

    def test_company_1(self):
        self.assertEqual(
            self.product_company_1.with_user(self.user_company_1).company_id,
            self.company_1,
        )
        # All of this should be allowed
        self.product_company_1.with_user(
            self.user_company_1
        ).description_sale = "Test 1"
        self.product_company_both.with_user(
            self.user_company_1
        ).description_sale = "Test 2"
        # And this one not
        with self.assertRaises(AccessError):
            self.product_company_2.with_user(
                self.user_company_1
            ).description_sale = "Test 3"

    def test_company_2(self):
        self.assertEqual(
            self.product_company_2.with_user(self.user_company_2).company_id,
            self.company_2,
        )
        # All of this should be allowed
        self.product_company_2.with_user(
            self.user_company_2
        ).description_sale = "Test 1"
        self.product_company_both.with_user(
            self.user_company_2
        ).description_sale = "Test 2"
        # And this one not
        with self.assertRaises(AccessError):
            self.product_company_1.with_user(
                self.user_company_2
            ).description_sale = "Test 3"

    def test_uninstall(self):
        from ..hooks import uninstall_hook

        uninstall_hook(self.env.cr, None)
        rule = self.env.ref("product.product_comp_rule")
        domain = (
            " ['|', ('company_id', '=', user.company_id.id), "
            "('company_id', '=', False)]"
        )
        self.assertEqual(rule.domain_force, domain)
