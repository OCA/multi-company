# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2021 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import AccessError, UserError
from odoo.fields import Command
from odoo.tests import common

from .common import ProductMultiCompanyCommon


class TestProductMultiCompany(ProductMultiCompanyCommon, common.TransactionCase):
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

    def test_allow_company_change(self):
        product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "company_ids": [(6, 0, [self.company_1.id, self.company_2.id])],
            }
        )
        product.write({"company_ids": [(3, self.company_2.id)]})
        self.assertNotIn(self.company_2.id, product.company_ids.ids)
        self.assertIn(self.company_1.id, product.company_ids.ids)

    def test_prevent_company_change_with_stock_moves(self):
        product = self.env["product.product"].create(
            {
                "name": "Test Product with Moves",
                "type": "product",
                "company_ids": [(6, 0, [self.company_1.id, self.company_2.id])],
            }
        )
        self.env["stock.move"].create(
            {
                "name": "Test Move",
                "product_id": product.id,
                "company_id": self.company_2.id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "product_uom_qty": 10,
                "product_uom": self.env.ref("uom.product_uom_unit").id,
            }
        )
        with self.assertRaises(UserError):
            product.company_ids = self.company_1

    def test_prevent_company_change_with_quantities(self):
        product = self.env["product.product"].create(
            {
                "name": "Test Product with Quantities",
                "type": "product",
                "company_ids": [(6, 0, [self.company_1.id, self.company_2.id])],
            }
        )
        location_company_2 = self.env["stock.location"].create(
            {
                "name": "Company 2 Stock Location",
                "usage": "internal",
                "company_id": self.company_2.id,
            }
        )
        self.env["stock.quant"].create(
            {
                "product_id": product.id,
                "company_id": self.company_2.id,
                "location_id": location_company_2.id,
                "quantity": 10,
            }
        )
        with self.assertRaises(UserError):
            product.write({"company_ids": [(3, self.company_2.id)]})

    def test_replace_company_ids(self):
        product = self.env["product.product"].create(
            {
                "name": "Test Product with Quantities",
                "type": "product",
                "company_ids": [(6, 0, [self.company_1.id, self.company_2.id])],
            }
        )
        location_company_2 = self.env["stock.location"].create(
            {
                "name": "Company 2 Stock Location",
                "usage": "internal",
                "company_id": self.company_2.id,
            }
        )
        self.env["stock.quant"].create(
            {
                "product_id": product.id,
                "company_id": self.company_2.id,
                "location_id": location_company_2.id,
                "quantity": 10,
            }
        )
        with self.assertRaises(UserError):
            product.write({"company_ids": [Command.set([self.company_1.id])]})

    def test_allow_all_companies(self):
        product = self.env["product.product"].create(
            {
                "name": "Test Product All Companies",
                "type": "product",
                "company_ids": [(6, 0, [self.company_1.id])],
            }
        )
        # Setting company_ids to False (allow all companies)
        product.company_ids = False
        self.assertFalse(product.company_ids)
        product.write({"company_ids": [Command.link(self.company_1.id)]})
