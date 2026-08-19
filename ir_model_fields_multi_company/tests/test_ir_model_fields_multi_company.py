from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, new_test_user


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
        cls.user = new_test_user(
            cls.env,
            login="mc_write_test_user",
            groups="base.group_user,base.group_partner_manager",
            company_id=cls.company_sf.id,
            company_ids=[Command.set((cls.company_sf | cls.company_chicago).ids)],
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
        """Any field of a record of an available company can be edited."""
        partner = self._as_user(self.partner_sf, self.company_sf)
        partner.write({"name": "Partner SF Renamed", "phone": "+111"})
        self.assertEqual(
            partner.name,
            "Partner SF Renamed",
            "Unrestricted field must be written on an available company record",
        )
        self.assertEqual(
            partner.phone,
            "+111",
            "Unrestricted field must be written on an available company record",
        )

    def test_02_foreign_company_allowed_field(self):
        """A flagged field can be edited on another company's record."""
        partner = self._as_user(self.partner_chicago, self.company_sf)
        partner.write({"ref": "CHI-REF"})
        self.assertEqual(
            partner.ref,
            "CHI-REF",
            "Field flagged as allowed must be written on a foreign record",
        )

    def test_03_foreign_company_forbidden_field(self):
        """A non-flagged field on another company's record raises UserError."""
        partner = self._as_user(self.partner_chicago, self.company_sf)
        with self.assertRaisesRegex(UserError, "Phone"):
            partner.write({"phone": "+222"})

    def test_04_foreign_company_mixed_vals(self):
        """Mixed vals raise and list all forbidden fields; nothing is written."""
        partner = self._as_user(self.partner_chicago, self.company_sf)
        with self.assertRaises(UserError) as cm:
            partner.write(
                {"ref": "CHI-REF", "phone": "+222", "website": "https://x.test"}
            )
        self.assertIn(
            "Phone", str(cm.exception), "Forbidden field must be listed in the error"
        )
        self.assertIn(
            "Website", str(cm.exception), "Forbidden field must be listed in the error"
        )
        self.assertNotIn(
            "Reference",
            str(cm.exception),
            "Allowed field must not be listed in the error",
        )
        self.assertFalse(
            self.partner_chicago.ref,
            "No partial application: the allowed field must not be written",
        )

    def test_05_record_without_company(self):
        """Records without company are not restricted."""
        partner = self._as_user(self.partner_shared, self.company_sf)
        partner.write({"name": "Shared Renamed", "phone": "+333"})
        self.assertEqual(
            partner.name,
            "Shared Renamed",
            "Record without company must not be restricted",
        )

    def test_06_record_company_among_available(self):
        """No restriction when the record's company is among env.companies."""
        companies = self.company_sf | self.company_chicago
        partner = self._as_user(self.partner_chicago, companies)
        partner.write({"phone": "+444"})
        self.assertEqual(
            partner.phone,
            "+444",
            "Record of an available company must not be restricted",
        )

    def test_07_multi_record_write(self):
        """In a multi-record write the foreign record still triggers the check."""
        records = self.partner_sf | self.partner_chicago
        partners = self._as_user(records, self.company_sf)
        with self.assertRaisesRegex(UserError, "Phone"):
            partners.write({"phone": "+555"})
        partners.write({"ref": "BOTH-REF"})
        self.assertEqual(
            self.partner_sf.ref, "BOTH-REF", "Allowed field must be written"
        )
        self.assertEqual(
            self.partner_chicago.ref, "BOTH-REF", "Allowed field must be written"
        )

    def test_08_flag_toggle_changes_outcome(self):
        """Toggling the flag changes the outcome of the same write."""
        partner = self._as_user(self.partner_chicago, self.company_sf)
        with self.assertRaisesRegex(UserError, "Phone"):
            partner.write({"phone": "+666"})
        self.field_phone.allow_multi_company_write = True
        partner.write({"phone": "+666"})
        self.assertEqual(
            partner.phone, "+666", "Field must be writable after enabling the flag"
        )
        self.field_phone.allow_multi_company_write = False
        with self.assertRaisesRegex(UserError, "Phone"):
            partner.write({"phone": "+777"})

    def test_09_technical_fields_ignored(self):
        """Technical fields never trigger the check nor appear in the error."""
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
        self.assertEqual(
            partner.ref,
            "CHI-REF-2",
            "Allowed field write must not fail because of log access fields",
        )
        with self.assertRaises(UserError) as cm:
            partner.write({"phone": "+888"})
        self.assertNotIn(
            "write_date",
            str(cm.exception),
            "Technical fields must not be listed in the error",
        )
        self.assertNotIn(
            "write_uid",
            str(cm.exception),
            "Technical fields must not be listed in the error",
        )

    def test_10_no_whitelist_no_restrictions(self):
        """Without any flagged field on the model, standard behavior applies."""
        self.field_ref.allow_multi_company_write = False
        partner = self._as_user(self.partner_chicago, self.company_sf)
        partner.write({"phone": "+999"})
        self.assertEqual(
            partner.phone,
            "+999",
            "Model without flagged fields must not be restricted",
        )

    def test_11_superuser_bypasses_check(self):
        """Superuser (env.su) writes are never restricted."""
        partner = self._as_user(self.partner_chicago, self.company_sf).sudo()
        partner.write({"phone": "+000"})
        self.assertEqual(
            partner.phone, "+000", "Superuser write must not be restricted"
        )
