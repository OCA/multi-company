# Copyright 2021 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestProductPricelistPerCompany(TransactionCase):
    def test_create_pricelist(self):
        ProductPricelist = self.env["product.pricelist"]
        vals = {
            "name": "Demo",
            "company_id": False,
        }
        # Create a global pricelist should fail
        with self.assertRaises(ValidationError):
            ProductPricelist.create(vals)

        # Create a pricelist related to a company should success
        vals.update({"company_id": self.env.ref("base.main_company").id})
        ProductPricelist.create(vals)
