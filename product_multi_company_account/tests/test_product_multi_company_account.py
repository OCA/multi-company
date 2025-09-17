# Copyright 2025 ForgeFlow S.L.
#   (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestProductMultiCompanyAccount(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_2 = cls.env["res.company"].create(
            {
                "name": "Test Company 2",
            }
        )
        cls.user_company_1 = cls.env["res.users"].create(
            {
                "name": "User Company 1",
                "login": "user_company_1",
                "groups_id": [(6, 0, [cls.env.ref("base.group_system").id])],
                "company_id": cls.company_data["company"].id,
                "company_ids": [(6, 0, [cls.company_data["company"].id])],
            }
        )
        cls.user_company_2 = cls.env["res.users"].create(
            {
                "name": "User Company 2",
                "login": "user_company_2",
                "groups_id": [(6, 0, [cls.env.ref("base.group_system").id])],
                "company_id": cls.company_2.id,
                "company_ids": [(6, 0, [cls.company_2.id])],
            }
        )

    def test_tax_access_during_product_creation(self):
        product_no_company = (
            self.env["product.template"]
            .with_user(self.user_company_1)
            .create(
                {
                    "name": "Test Product No Company",
                    "list_price": 300.0,
                }
            )
        )
        self.assertTrue(
            product_no_company, "Product creation without company should succeed"
        )
        self.assertFalse(
            product_no_company.company_id, "Product should have no specific company"
        )
