from odoo.tests import common


class TestIrConfigParameterMultiCompany(common.TransactionCase):
    def test_basic_functionality(self):
        record = self.env["ir.config_parameter"].create(
            {"key": "testKey", "value": "testValue"}
        )
        value = record.get_param("testKey")
        expected_field_value = "testValue"
        self.assertEqual(value, expected_field_value)

    def test_get_params(self):
        testCompany = self.env["res.company"].create({"name": "TestCompany"})
        record = self.env["ir.config_parameter"].create(
            {
                "key": "mail.catchall.alias_test",
                "value": "testValue",
                "company_value_ids": [
                    (
                        0,
                        0,
                        {
                            "company_id": self.env.company.id,
                            "company_value": "CurrentCompany",
                        },
                    ),
                    (
                        0,
                        0,
                        {"company_id": testCompany.id, "company_value": "TestCompany"},
                    ),
                ],
            }
        )
        value = record.get_param("mail.catchall.alias_test")
        self.assertEqual(value, "CurrentCompany")
        self.env.user.company_id = testCompany.id
        value = record.get_param("mail.catchall.alias_test")
        self.assertEqual(value, "TestCompany")
