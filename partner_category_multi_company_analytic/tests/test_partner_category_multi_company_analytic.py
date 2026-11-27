# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import new_test_user, tagged

from odoo.addons.analytic.tests.common import AnalyticCommon


@tagged("post_install", "-at_install")
class TestPartnerCategoryMultiCompanyAnalytic(AnalyticCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "Company B"})
        cls.Category = cls.env["res.partner.category"]
        cls.tag_a = cls.Category.create(
            {"name": "Tag A", "company_id": cls.company_a.id}
        )
        cls.tag_b = cls.Category.create(
            {"name": "Tag B", "company_id": cls.company_b.id}
        )
        cls.tag_shared = cls.Category.create({"name": "Tag Shared"})
        cls.DistributionModel = cls.env["account.analytic.distribution.model"]
        cls.distribution = {cls.analytic_account_3.id: 100}

    def _create_models(self, vals_list):
        return self.DistributionModel.create(
            [dict(vals, analytic_distribution=self.distribution) for vals in vals_list]
        )

    def test_partner_category_company_check(self):
        cases = [
            (self.company_a, self.tag_a, True),
            (self.company_a, self.tag_shared, True),
            (self.DistributionModel.company_id, self.tag_shared, True),
            (self.company_a, self.tag_b, False),
            (self.DistributionModel.company_id, self.tag_a, False),
        ]
        for company, tag, allowed in cases:
            with self.subTest(company=company.name, tag=tag.name):
                vals = {"company_id": company.id, "partner_category_id": tag.id}
                if allowed:
                    model = self._create_models([vals])
                    self.assertEqual(model.partner_category_id, tag)
                else:
                    with self.assertRaises(UserError):
                        self._create_models([vals])

    def test_multi_record_and_company_change(self):
        models = self._create_models(
            [
                {"company_id": self.company_a.id, "partner_category_id": self.tag_a.id},
                {"company_id": self.company_b.id, "partner_category_id": self.tag_b.id},
            ]
        )
        self.assertEqual(models.partner_category_id, self.tag_a | self.tag_b)
        with self.assertRaises(UserError):
            self._create_models(
                [
                    {
                        "company_id": self.company_b.id,
                        "partner_category_id": self.tag_b.id,
                    },
                    {
                        "company_id": self.company_a.id,
                        "partner_category_id": self.tag_b.id,
                    },
                ]
            )
        for company in (self.company_b, self.DistributionModel.company_id):
            with self.subTest(company=company.name), self.assertRaises(UserError):
                models[0].company_id = company

    def test_non_admin_user(self):
        user = new_test_user(
            self.env,
            login="analytic_tag_user",
            groups="base.group_user,analytic.group_analytic_accounting",
            company_id=self.company_a.id,
            company_ids=[Command.set((self.company_a | self.company_b).ids)],
        )
        model = (
            self.DistributionModel.with_user(user)
            .with_company(self.company_a)
            .create(
                {
                    "partner_category_id": self.tag_a.id,
                    "analytic_distribution": self.distribution,
                }
            )
        )
        self.assertEqual(model.company_id, self.company_a)
        with self.assertRaises(UserError):
            model.partner_category_id = self.tag_b

    def test_field_domain(self):
        domain = self.DistributionModel.fields_get(["partner_category_id"], ["domain"])[
            "partner_category_id"
        ]["domain"]
        self.assertIn("company_id", domain)
