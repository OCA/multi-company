# Copyright 2021-2025 Tecnativa - Víctor Martínez
# Copyright 2022 Moduon - Eduardo de Miguel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import Command
from odoo.tests import Form, new_test_user, tagged
from odoo.tests.common import users

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestEasyCreation(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref("base.user_admin").write(
            {
                "groups_id": [
                    Command.link(cls.env.ref("account.group_account_manager").id),
                    Command.link(cls.env.ref("account.group_account_user").id),
                ],
            }
        )
        cls.test_user = new_test_user(
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
        cls.test_extra_user = new_test_user(cls.env, login="test-extra-user")
        cls.sale_tax = cls.env["account.tax"].create(
            {"name": "Test sale tax", "type_tax_use": "sale"}
        )
        cls.purchase_tax = cls.env["account.tax"].create(
            {"name": "Test purchase tax", "type_tax_use": "purchase"}
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test product",
                "taxes_id": [Command.set(cls.sale_tax.ids)],
                "supplier_taxes_id": [Command.set(cls.purchase_tax.ids)],
            }
        )
        cls.sale_product = cls.env["product.product"].create(
            {
                "name": "Test sale product",
                "taxes_id": [Command.set(cls.sale_tax.ids)],
            }
        )
        cls.purchase_product = cls.env["product.product"].create(
            {
                "name": "Test purchase product",
                "supplier_taxes_id": [Command.set(cls.purchase_tax.ids)],
            }
        )
        cls.extra_product = cls.env["product.product"].create(
            {
                "name": "Test extra product",
            }
        )
        cls.bank = cls.env["res.bank"].create({"name": "Test bank"})

    def _test_model_items(self, model, company):
        env_model = self.env[model]
        f_name = "company_ids" if "company_ids" in env_model._fields else "company_id"
        self.assertGreaterEqual(env_model.search_count([(f_name, "=", company.id)]), 1)

    def test_wizard_easy_creation(self):
        wizard_form = Form(
            self.env["account.multicompany.easy.creation.wiz"].with_context(
                allowed_company_ids=self.env.company.ids
            )
        )
        wizard_form.name = "test_company"
        wizard_form.chart_template = "generic_coa"
        wizard_form.smart_search_product_tax = True
        wizard_form.update_default_taxes = True
        wizard_form.default_sale_tax = "generic_coa-sale_tax_template"
        wizard_form.force_sale_tax = True
        wizard_form.default_purchase_tax = "generic_coa-purchase_tax_template"
        wizard_form.force_purchase_tax = True
        wizard_form.user_ids.add(self.test_user)
        wizard_form.user_ids.add(self.test_extra_user)
        with wizard_form.bank_ids.new() as bank_line_form:
            bank_line_form.acc_number = "acc_number-1"
            bank_line_form.bank_id = self.bank
        with wizard_form.bank_ids.new() as bank_line_form:
            bank_line_form.acc_number = "acc_number-2"
            bank_line_form.bank_id = self.bank
        record = wizard_form.save()
        record.action_accept()
        self.assertEqual(record.new_company_id.name, "test_company")
        self.assertEqual(record.new_company_id.chart_template, "generic_coa")
        self.assertIn(record.new_company_id, self.test_user.company_ids)
        self.assertIn(record.new_company_id, self.test_extra_user.company_ids)
        # Some misc validations
        self._test_model_items("account.tax", record.new_company_id)
        self._test_model_items("account.account", record.new_company_id)
        self._test_model_items("account.journal", record.new_company_id)
        # Ir default records
        IrDefault = self.env["ir.default"].sudo()
        value = IrDefault._get(
            "product.template", "taxes_id", company_id=record.new_company_id.id
        )
        self.assertEqual(value, record.new_company_id.account_sale_tax_id.ids)
        value = IrDefault._get(
            "product.template", "supplier_taxes_id", company_id=record.new_company_id.id
        )
        self.assertEqual(value, record.new_company_id.account_purchase_tax_id.ids)
        # Product taxes
        self.assertGreater(len(self.product.taxes_id), 1)
        self.assertGreater(len(self.product.supplier_taxes_id), 1)
        self.assertGreater(len(self.sale_product.taxes_id), 1)
        self.assertGreater(len(self.purchase_product.supplier_taxes_id), 1)
        # bank_journals
        bank_journals = self.env["account.journal"].search(
            [("type", "=", "bank"), ("company_id", "=", record.new_company_id.id)]
        )
        self.assertEqual(len(bank_journals), 2)
        self.assertIn("acc_number-1", bank_journals.mapped("bank_acc_number"))
        self.assertIn("acc_number-2", bank_journals.mapped("bank_acc_number"))

    @users("test-user")
    def test_wizard_easy_creation_test_user(self):
        self.test_wizard_easy_creation()
