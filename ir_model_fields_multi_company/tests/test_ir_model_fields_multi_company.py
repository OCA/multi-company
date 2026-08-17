# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestIrModelFieldsMultiCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_sf = cls.env["res.company"].create(
            {"name": "Multi-Company Write Test SF"}
        )
        cls.company_chicago = cls.env["res.company"].create(
            {"name": "Multi-Company Write Test Chicago"}
        )
        cls.user = cls.env["res.users"].create(
            {
                "name": "Multi-Company Test User",
                "login": "mc_write_test_user",
                "company_id": cls.company_sf.id,
                "company_ids": [
                    Command.set([cls.company_sf.id, cls.company_chicago.id])
                ],
                "groups_id": [
                    Command.set(
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("base.group_partner_manager").id,
                        ]
                    )
                ],
            }
        )
        # The module targets records made visible through custom record
        # rules; neutralize the standard partner multi-company rule so the
        # tests exercise only this module's own check.
        cls.env.ref("base.res_partner_rule").active = False
        cls.partner_sf = cls.env["res.partner"].create(
            {"name": "Partner SF", "company_id": cls.company_sf.id}
        )
        cls.partner_chicago = cls.env["res.partner"].create(
            {"name": "Partner Chicago", "company_id": cls.company_chicago.id}
        )
        cls.partner_shared = cls.env["res.partner"].create({"name": "Partner Shared"})
        cls.field_ref = cls.env["ir.model.fields"]._get("res.partner", "ref")
        cls.field_phone = cls.env["ir.model.fields"]._get("res.partner", "phone")
        cls.field_ref.allow_multi_company_write = True

    def _as_user(self, records, companies):
        """Return `records` as the test user restricted to `companies`."""
        return records.with_user(self.user).with_context(
            allowed_company_ids=companies.ids
        )

    def test_01_own_company_no_restrictions(self):
        partner = self._as_user(self.partner_sf, self.company_sf)
        partner.write({"name": "Partner SF Renamed", "phone": "+111"})
        self.assertEqual(partner.name, "Partner SF Renamed")
        self.assertEqual(partner.phone, "+111")

    def test_02_foreign_company_allowed_field(self):
        partner = self._as_user(self.partner_chicago, self.company_sf)
        partner.write({"ref": "CHI-REF"})
        self.assertEqual(partner.ref, "CHI-REF")

    def test_03_foreign_company_forbidden_field(self):
        partner = self._as_user(self.partner_chicago, self.company_sf)
        with self.assertRaisesRegex(UserError, "Phone"):
            partner.write({"phone": "+222"})

    def test_04_foreign_company_mixed_vals(self):
        partner = self._as_user(self.partner_chicago, self.company_sf)
        with self.assertRaises(UserError) as cm:
            partner.write(
                {"ref": "CHI-REF", "phone": "+222", "website": "https://x.test"}
            )
        self.assertIn("Phone", str(cm.exception))
        self.assertIn("Website", str(cm.exception))
        self.assertNotIn("Reference", str(cm.exception))
        # No partial application: the allowed field was not written either.
        self.assertFalse(self.partner_chicago.ref)

    def test_05_record_without_company(self):
        partner = self._as_user(self.partner_shared, self.company_sf)
        partner.write({"name": "Shared Renamed", "phone": "+333"})
        self.assertEqual(partner.name, "Shared Renamed")

    def test_06_record_company_among_available(self):
        companies = self.company_sf | self.company_chicago
        partner = self._as_user(self.partner_chicago, companies)
        partner.write({"phone": "+444"})
        self.assertEqual(partner.phone, "+444")

    def test_07_multi_record_write(self):
        records = self.partner_sf | self.partner_chicago
        partners = self._as_user(records, self.company_sf)
        with self.assertRaisesRegex(UserError, "Phone"):
            partners.write({"phone": "+555"})
        partners.write({"ref": "BOTH-REF"})
        self.assertEqual(self.partner_sf.ref, "BOTH-REF")
        self.assertEqual(self.partner_chicago.ref, "BOTH-REF")

    def test_08_flag_toggle_changes_outcome(self):
        partner = self._as_user(self.partner_chicago, self.company_sf)
        with self.assertRaisesRegex(UserError, "Phone"):
            partner.write({"phone": "+666"})
        self.field_phone.allow_multi_company_write = True
        partner.write({"phone": "+666"})
        self.assertEqual(partner.phone, "+666")
        self.field_phone.allow_multi_company_write = False
        with self.assertRaisesRegex(UserError, "Phone"):
            partner.write({"phone": "+777"})

    def test_09_technical_fields_ignored(self):
        partner = self._as_user(self.partner_chicago, self.company_sf)
        # Service keys added by the ORM itself must not trigger the check.
        partner._check_allow_multi_company_write(
            {
                "write_date": fields.Datetime.now(),
                "write_uid": self.user.id,
                "parent_path": "1/",
                "__last_update": fields.Datetime.now(),
            }
        )
        # A regular write of an allowed field must not fail because of the
        # automatic write_date / write_uid update.
        partner.write({"ref": "CHI-REF-2"})
        self.assertEqual(partner.ref, "CHI-REF-2")
        with self.assertRaises(UserError) as cm:
            partner.write({"phone": "+888"})
        self.assertNotIn("write_date", str(cm.exception))
        self.assertNotIn("write_uid", str(cm.exception))

    def test_10_no_whitelist_no_restrictions(self):
        self.field_ref.allow_multi_company_write = False
        partner = self._as_user(self.partner_chicago, self.company_sf)
        partner.write({"phone": "+999"})
        self.assertEqual(partner.phone, "+999")

    def test_11_superuser_bypasses_check(self):
        partner = self._as_user(self.partner_chicago, self.company_sf).sudo()
        partner.write({"phone": "+000"})
        self.assertEqual(partner.phone, "+000")
