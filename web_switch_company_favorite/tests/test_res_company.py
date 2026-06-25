# Copyright 2026 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
# @author Pierre Verkest <pierre@verkest.fr>

from odoo.tests.common import TransactionCase


class TestResCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env["res.company"].create({"name": "Company A"})
        cls.company_b = cls.env["res.company"].create({"name": "Company B"})

        cls.test_user = cls.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_user",
                "company_id": cls.company_a.id,
                "company_ids": [(6, 0, [cls.company_a.id])],
                "group_ids": [(6, 0, cls.env.ref("base.group_user").ids)],
            }
        )

        cls.filter_all = cls.env["ir.filters"].create(
            {
                "name": "All Companies",
                "model_id": "res.company",
                "domain": "[]",
            }
        )
        cls.filter_company_b = cls.env["ir.filters"].create(
            {
                "name": "Company B",
                "model_id": "res.company",
                "domain": "[('name', '=', 'Company B')]",
            }
        )
        cls.filter_other_model = cls.env["ir.filters"].create(
            {
                "name": "Other Model",
                "model_id": "res.partner",
                "domain": "[]",
            }
        )

    def test_get_companies_from_filter_returns_only_allowed_companies(self):
        companies = (
            self.env["res.company"]
            .with_user(self.test_user)
            .get_companies_from_filter(self.filter_all.id)
        )
        self.assertEqual(companies, [self.company_a.id])

    def test_get_companies_from_filter_with_non_matching_filter_returns_empty(self):
        companies = (
            self.env["res.company"]
            .with_user(self.test_user)
            .get_companies_from_filter(self.filter_company_b.id)
        )
        self.assertEqual(companies, [])

    def test_get_companies_from_filter_with_invalid_filter_id_returns_empty(self):
        companies = self.env["res.company"].get_companies_from_filter(999999)
        self.assertEqual(companies, [])

    def test_get_companies_from_filter_with_wrong_model_filter_returns_empty(self):
        companies = self.env["res.company"].get_companies_from_filter(
            self.filter_other_model.id
        )
        self.assertEqual(companies, [])
