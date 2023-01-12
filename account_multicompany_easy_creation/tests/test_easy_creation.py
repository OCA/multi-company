# Copyright 2021-2022 Tecnativa - Víctor Martínez
# Copyright 2022 Moduon - Eduardo de Miguel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.tests import Form, common, new_test_user
from odoo.tests.common import users


class TestEasyCreation(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref("base.user_admin").write(
            {
                "groups_id": [
                    (4, cls.env.ref("account.group_account_manager").id),
                    (4, cls.env.ref("account.group_account_user").id),
                ],
            }
        )
        new_test_user(
            cls.env,
            login="test-user",
            groups=",".join(
                [
                    "account.group_account_manager",
                    "account.group_account_user",
                    "base.group_system",
                    "base.group_partner_manager",
                ]
            ),
        )
        cls.chart_template_id = cls.env["account.chart.template"].search([], limit=1)
        cls.sale_tax_template = cls.env["account.tax.template"].search(
            [("type_tax_use", "=", "sale")], limit=1
        )
        cls.purchase_tax_template = cls.env["account.tax.template"].search(
            [("type_tax_use", "=", "purchase")], limit=1
        )

    def _test_model_items(self, model, company_id):
        self.assertGreaterEqual(
            self.env[model].search_count([("company_id", "=", company_id.id)]), 1
        )

    def test_wizard_easy_creation(self):
        wizard_form = Form(
            self.env["account.multicompany.easy.creation.wiz"].with_context(
                allowed_company_ids=self.env.company.ids
            )
        )
        wizard_form.name = "test_company"
        wizard_form.chart_template_id = self.chart_template_id
        wizard_form.smart_search_product_tax = True
        wizard_form.update_default_taxes = True
        wizard_form.force_sale_tax = True
        wizard_form.force_purchase_tax = True
        wizard_form.default_purchase_tax_id = self.purchase_tax_template
        wizard_form.default_sale_tax_id = self.sale_tax_template
        for user in self.env["res.users"].search([]):
            wizard_form.user_ids.add(user)
        record = wizard_form.save()
        record.action_accept()
        self.assertEqual(record.new_company_id.name, "test_company")
        self.assertEqual(
            record.new_company_id.chart_template_id, self.chart_template_id
        )
        # Some misc validations
        self._test_model_items("account.tax", record.new_company_id)
        self._test_model_items("account.account", record.new_company_id)
        self._test_model_items("account.journal", record.new_company_id)

    @users("test-user")
    def test_wizard_easy_creation_test_user(self):
        self.test_wizard_easy_creation()
