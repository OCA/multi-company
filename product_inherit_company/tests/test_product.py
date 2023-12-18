#  Copyright 2023 Simone Rubino - Aion Tech
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from odoo.addons.base_inherit_company.tests.common import Common


class TestProduct(Common):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_model = cls.env["product.template"]

    def test_inherit_company(self):
        """Products created for an element of a family of companies
        are shared to all the companies"""
        # Arrange: A family of companies
        companies = self.parent_company | self.child_company | self.sibling_company

        # Act: Create a product for each company
        products = self.product_model.browse()
        for company in companies:
            product_form = Form(self.product_model.with_company(self.parent_company))
            product_form.name = "Product of " + company.name
            product_form.company_ids.clear()
            product_form.company_ids.add(company)
            product = product_form.save()
            products |= product

        # Assert: All created products are shared to every element of the family
        for product in products:
            self.assertEqual(product.company_ids, companies)
