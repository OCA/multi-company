# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.tests import Form, common


class TestEasyCreation(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env.ref("base.user_admin")
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
            self.env["account.multicompany.easy.creation.wiz"].with_user(self.user)
        )
        wizard_form.name = "test_company"
        wizard_form.default_purchase_tax_id = self.purchase_tax_template
        wizard_form.chart_template_id = self.chart_template_id
        wizard_form.update_default_taxes = True
        wizard_form.smart_search_product_tax = True
        wizard_form.force_sale_tax = True
        wizard_form.force_purchase_tax = True
        wizard_form.default_sale_tax_id = self.sale_tax_template
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
