# Copyright 2025 ForgeFlow S.L.
#   (http://www.forgeflow.com)
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
