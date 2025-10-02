# Copyright 2025 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import common

from .common import ProductPackagingMultiCompanyCommon


class TestProductPackagingMultiCompany(
    ProductPackagingMultiCompanyCommon, common.TransactionCase
):
    def test_create_packaging_default_company(self):
        packaging = self.env["product.packaging"].create({"name": "Test Packaging"})
        self.assertIn(self.env.company.id, packaging.company_ids.ids)

    def test_packaging_company_none(self):
        self.assertFalse(self.packaging_company_none.company_id)
        self.packaging_company_none.with_user(self.user_company_1).barcode = "PK1"
        self.packaging_company_none.with_user(self.user_company_2).barcode = "PK2"

    def test_packaging_company_1_access(self):
        self.assertEqual(
            self.packaging_company_1.with_user(self.user_company_1).company_id,
            self.company_1,
        )
        self.packaging_company_1.with_user(self.user_company_1).barcode = "OK"
        self.packaging_company_both.with_user(self.user_company_1).barcode = "OK2"
        with self.assertRaises(AccessError):
            self.packaging_company_2.with_user(self.user_company_1).barcode = "FAIL"

    def test_packaging_company_2_access(self):
        self.assertEqual(
            self.packaging_company_2.with_user(self.user_company_2).company_id,
            self.company_2,
        )
        self.packaging_company_2.with_user(self.user_company_2).barcode = "OK"
        self.packaging_company_both.with_user(self.user_company_2).barcode = "OK2"
        with self.assertRaises(AccessError):
            self.packaging_company_1.with_user(self.user_company_2).barcode = "FAIL"

    def test_packaging_package_type_constraint(self):
        with self.assertRaises(ValidationError):
            self.env["product.packaging"].create(
                {
                    "name": "Invalid Packaging",
                    "company_ids": [(6, 0, self.company_2.ids)],
                    "package_type_id": self.package_type_company_1.id,
                }
            )
