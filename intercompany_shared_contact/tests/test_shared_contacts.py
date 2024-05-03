#  Copyright (c) Akretion 2021
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from odoo_test_helper import FakeModelLoader

from odoo.exceptions import AccessError
from odoo.tests import SavepointCase


class IntercompanySharedContactCase(SavepointCase, FakeModelLoader):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Load fake models ->/
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models import ResPartner

        cls.loader.update_registry([ResPartner])
        # ->/ Load fake models

        cls.company_x = cls.env["res.company"].create({"name": "x Company"})
        cls.partner_x = cls.company_x.partner_id
        cls.user_x = cls.env["res.users"].create(
            {
                "name": "x user",
                "company_ids": [cls.company_x.id],
                "company_id": cls.company_x.id,
                "login": "x",
            }
        )

        cls.company_y = cls.env["res.company"].create({"name": "y Company"})
        cls.partner_y = cls.company_y.partner_id
        cls.user_y = cls.env["res.users"].create(
            {
                "name": "y user",
                "company_ids": [cls.company_y.id],
                "company_id": cls.company_y.id,
                "login": "y",
            }
        )
        cls.contact_y = cls.user_y.partner_id
        cls.address_y = cls.env["res.partner"].create(
            {
                "name": "Foo address",
                "parent_id": cls.partner_y.id,
            }
        )
        cls.partner_other = cls.env.ref("base.res_partner_12")
        cls.partner_other.company_id = cls.company_x

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def test_computed_fields(self):
        self.assertEqual(self.partner_x.res_company_id, self.company_x)
        self.assertEqual(self.partner_x.origin_company_id, self.company_x)

        self.assertEqual(self.partner_y.res_company_id, self.company_y)
        self.assertEqual(self.partner_y.origin_company_id, self.company_y)
        self.assertEqual(self.contact_y.origin_company_id, self.company_y)
        self.assertEqual(self.address_y.origin_company_id, self.company_y)

    def test_intercompany_read(self):
        """
        Company partner are readable by other companies
        """
        self.env["res.partner"].with_user(self.user_x).browse(self.partner_y.id).name
        self.env["res.partner"].with_user(self.user_x).browse(self.contact_y.id).name
        self.env["res.partner"].with_user(self.user_x).browse(self.address_y.id).name
        self.env["res.partner"].with_user(self.user_y).browse(self.partner_x.id).name

    def test_partner_intercompany_update(self):
        """
        Company partner are not-editable by other companies
        """
        partner_y = self.partner_y.with_user(self.user_x)
        with self.assertRaises(AccessError):
            partner_y.name = "boom"

    def test_contact_intercompany_create(self):
        """
        Company contact are not-creatable by other companies
        """
        with self.assertRaises(AccessError):
            self.env["res.partner"].with_user(self.user_x).create(
                {
                    "name": "Foo new address",
                    "parent_id": self.partner_y.id,
                }
            )

    def test_contact_intercompany_update(self):
        """
        Company contact are not-editable by other companies
        """
        with self.assertRaises(AccessError):
            self.contact_y.with_user(self.user_x).name = "boom"

        with self.assertRaises(AccessError):
            self.address_y.with_user(self.user_x).name = "boom"

    def test_contact_intercompany_unlink(self):
        """
        Company contact are not-deleteable by other companies
        """
        with self.assertRaises(AccessError):
            self.address_y.with_user(self.user_x).unlink()

    def test_intercompany_update_company_dependent(self):
        """
        Company dependent field of Company partner are modifiable by other companies
        """
        partner_y = self.partner_y.with_user(self.user_x)
        partner_y.barcode = "ça-fait-pas-boom"

    def test_intercompany_update_commercial_company_dependent(self):
        """
        Commercial (field sync with children) Company dependent field of Company
        contacts are modifiable by other companies
        """
        # We test with the field barcode because it's the only depenen
        partner_y = self.partner_y.with_user(self.user_x)
        partner_y.foo_company_dependent_field = "ça-fait-pas-boom"

    def test_intercompany_other(self):
        """
        Private, non-company-linked contacts are not shared
        """
        self.partner_other.company_id = self.company_x
        self.partner_other.invalidate_cache()
        with self.assertRaises(AccessError):
            self.partner_other.with_user(self.user_y).name

    def test_create_company(self):
        """
        User with admin access can create a company
        """
        self.user_x.groups_id |= self.env.ref("base.group_erp_manager")
        self.env["res.company"].with_user(self.user_x).create(
            {
                "name": "Company X bis",
            }
        )

    def test_update_company(self):
        """
        User with admin access can update a company
        """
        self.user_x.groups_id |= self.env.ref("base.group_erp_manager")
        self.company_x.with_user(self.user_x).write({"name": "FOO"})
