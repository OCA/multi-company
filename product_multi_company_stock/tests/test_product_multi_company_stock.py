# Copyright 2025-26 ForgeFlow S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError

from odoo.addons.product_multi_company.tests.test_product_multi_company import (
    TestProductMultiCompany,
)


class TestProductMultiCompanyStock(TestProductMultiCompany):
    def test_remove_company_with_quants_or_moves(self):
        product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "is_storable": True,
                "company_ids": [(6, 0, [self.company_1.id, self.company_2.id])],
            }
        )
        internal_loc = self.env["stock.location"].create(
            {
                "name": "Test Internal Location",
                "usage": "internal",
                "company_id": self.company_1.id,
            }
        )
        dest_loc = self.env["stock.location"].create(
            {
                "name": "Test Customer Location",
                "usage": "customer",
                "company_id": self.company_1.id,
            }
        )
        quant = self.env["stock.quant"].create(
            {
                "product_id": product.id,
                "location_id": internal_loc.id,
                "company_id": self.company_1.id,
                "quantity": 10,
            }
        )
        with self.assertRaises(UserError) as error_quant:
            product.write({"company_ids": [(6, 0, [self.company_2.id])]})
        self.assertIn("stock quantities", str(error_quant.exception))
        quant.unlink()
        move = self.env["stock.move"].create(
            {
                "name": "Test Stock Move",
                "product_id": product.id,
                "product_uom_qty": 10,
                "product_uom": product.uom_id.id,
                "location_id": internal_loc.id,
                "location_dest_id": dest_loc.id,
                "company_id": self.company_1.id,
            }
        )

        move._action_confirm()
        move._action_assign()
        move._action_done()
        with self.assertRaises(UserError) as error_move:
            product.write({"company_ids": [(6, 0, [self.company_2.id])]})
        self.assertIn("stock moves", str(error_move.exception))

    def test_remove_company_with_quants_or_moves_archived_product(self):
        product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "is_storable": True,
                "company_ids": [(6, 0, [self.company_1.id, self.company_2.id])],
                "active": False,
            }
        )
        internal_loc = self.env["stock.location"].create(
            {
                "name": "Test Internal Location",
                "usage": "internal",
                "company_id": self.company_1.id,
            }
        )
        dest_loc = self.env["stock.location"].create(
            {
                "name": "Test Customer Location",
                "usage": "customer",
                "company_id": self.company_1.id,
            }
        )
        quant = self.env["stock.quant"].create(
            {
                "product_id": product.id,
                "location_id": internal_loc.id,
                "company_id": self.company_1.id,
                "quantity": 10,
            }
        )
        with self.assertRaises(UserError) as error_quant:
            product.write({"company_ids": [(6, 0, [self.company_2.id])]})
        self.assertIn("stock quantities", str(error_quant.exception))
        quant.unlink()
        move = self.env["stock.move"].create(
            {
                "name": "Test Stock Move",
                "product_id": product.id,
                "product_uom_qty": 10,
                "product_uom": product.uom_id.id,
                "location_id": internal_loc.id,
                "location_dest_id": dest_loc.id,
                "company_id": self.company_1.id,
            }
        )

        move._action_confirm()
        move._action_assign()
        move._action_done()
        with self.assertRaises(UserError) as error_move:
            product.write({"company_ids": [(6, 0, [self.company_2.id])]})
        self.assertIn("stock moves", str(error_move.exception))

    def test_add_company_does_not_break_same_name_lots(self):
        """Adding a company to a product must not affect existing lots.

        Adding a new company to a product's company_ids triggers a
        recompute of stock.lot.company_id (which depends on product_id.company_id).
        should not change lots company.
        """
        product = self.env["product.product"].create(
            {
                "name": "Test Tracked Product",
                "is_storable": True,
                "tracking": "lot",
                "company_ids": [(6, 0, [self.company_1.id, self.company_2.id])],
            }
        )
        company_3 = self.company_obj.create({"name": "Test company 3"})
        lot_1 = (
            self.env["stock.lot"]
            .with_company(self.company_1)
            .create(
                {
                    "name": "LOT001",
                    "product_id": product.id,
                    "company_id": self.company_1.id,
                }
            )
        )
        lot_2 = (
            self.env["stock.lot"]
            .with_company(self.company_2)
            .create(
                {
                    "name": "LOT001",
                    "product_id": product.id,
                    "company_id": self.company_2.id,
                }
            )
        )
        # Adding a third company should neither raise nor alter the lot companies.
        product.write({"company_ids": [(4, company_3.id)]})
        self.assertEqual(lot_1.company_id, self.company_1)
        self.assertEqual(lot_2.company_id, self.company_2)
