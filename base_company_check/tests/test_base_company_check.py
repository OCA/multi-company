# Copyright 2022 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo_test_helper import FakeModelLoader

from odoo.exceptions import UserError
from odoo.tests.common import SavepointCase


class TestBaseCompanyCheck(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models import PrincipalModelFake, SecondaryModelFake

        cls.loader.update_registry((SecondaryModelFake, PrincipalModelFake))

        cls.company_1 = cls.env["res.company"].create({"name": "company 1"})
        cls.company_2 = cls.env["res.company"].create({"name": "company 2"})
        cls.primary_record = (
            cls.env["principal.model.fake"]
            .with_company(cls.company_1)
            .create({"name": "TEST", "company_id": cls.company_1.id})
        )

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def test_1_no_existing_record_in_company(self):
        self.primary_record.company_id = self.company_1
        self.primary_record.company_id = self.company_2

    def test_2_existing_record_in_company(self):
        self.env["secondary.model.fake"].create(
            {
                "name": "secondary record",
                "primary_id": self.primary_record.id,
                "company_id": self.company_1.id,
            }
        )
        with self.assertRaises(UserError) as m:
            self.primary_record.write({"company_id": self.company_2.id})
        self.assertEqual(
            m.exception.args[0],
            "It's not possible to set the company company 2 to the "
            "record TEST as it have been used by company 1",
        )
