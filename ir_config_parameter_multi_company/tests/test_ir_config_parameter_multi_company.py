from odoo.tests import common


class TestIrConfigParameterMultiCompany(common.TransactionCase):
    def setUp(self):
        super(TestIrConfigParameterMultiCompany, self).setUp()
        self.user = self.env.ref("base.user_demo")
        self.user.groups_id += self.env.ref("base.group_system")

    def test_get_params_base(self):

        record = (
            self.env["ir.config_parameter"]
            .with_user(self.user.id)
            .create({"key": "testKey", "value": "testValue"})
        )
        value = record.get_param("testKey")
        expected_field_value = "testValue"
        self.assertEqual(value, expected_field_value)

    def test_get_params_by_company(self):
        testCompany = self.env["res.company"].create({"name": "TestCompany"})
        self.user.company_ids += testCompany
        self.env["ir.config_parameter"].with_user(self.user.id).create(
            {
                "key": "mail.catchall.alias_test",
                "value": "CurrentCompany",
                "company_id": self.user.company_id.id,
            }
        )
        self.env["ir.config_parameter"].create(
            {
                "key": "mail.catchall.alias_test",
                "value": "testValue",
                "company_id": testCompany.id,
            }
        )
        value = (
            self.env["ir.config_parameter"]
            .with_user(self.user.id)
            .with_company(self.user.company_id)
            .get_param("mail.catchall.alias_test")
        )
        self.assertEqual(value, "CurrentCompany")
        self.user.company_id = testCompany.id
        value = (
            self.env["ir.config_parameter"]
            .with_user(self.user.id)
            .with_company(self.user.company_id)
            .get_param("mail.catchall.alias_test")
        )
        self.assertEqual(value, "testValue")
