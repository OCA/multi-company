# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestMailPartnerResolutionByCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "Company B"})
        cls.duplicate_email = "duplicate@test.example.com"
        cls.partner_company_a = cls.env["res.partner"].create(
            {
                "name": "Partner A",
                "email": "partner.a@test.example.com",
                "company_id": cls.company_a.id,
            }
        )
        cls.partner_company_b = cls.env["res.partner"].create(
            {
                "name": "Partner B",
                "email": "partner.b@test.example.com",
                "company_id": cls.company_b.id,
            }
        )
        cls.partner_no_company = cls.env["res.partner"].create(
            {
                "name": "Partner No Company",
                "email": "no.company@test.example.com",
                "company_id": False,
            }
        )
        cls.partner_company_a_duplicate = cls.env["res.partner"].create(
            {
                "name": "Partner A Duplicate",
                "email": cls.duplicate_email,
                "company_id": cls.company_a.id,
            }
        )
        cls.partner_company_b_duplicate = cls.env["res.partner"].create(
            {
                "name": "Partner B Duplicate",
                "email": cls.duplicate_email,
                "company_id": cls.company_b.id,
            }
        )
        cls.record_company_b = cls.env["res.partner"].create(
            {
                "name": "Record Company B",
                "company_id": cls.company_b.id,
            }
        )

    def _find_partners(self, company, emails, records=None, allowed_companies=None):
        allowed_companies = allowed_companies or [company]
        env = (
            self.env["res.partner"]
            .with_context(allowed_company_ids=[c.id for c in allowed_companies])
            .with_company(company)
        )
        return env._mail_find_partner_from_emails(emails, records=records)

    def test_include_same_company_partner(self):
        found = self._find_partners(self.company_a, [self.partner_company_a.email])
        self.assertEqual(found, [self.partner_company_a])

    def test_exclude_other_company_partner(self):
        found = self._find_partners(self.company_a, [self.partner_company_b.email])
        self.assertFalse(found[0])

    def test_include_no_company_partner(self):
        found = self._find_partners(self.company_a, [self.partner_no_company.email])
        self.assertEqual(found, [self.partner_no_company])

    def test_use_record_company_instead_of_env_company(self):
        found = self._find_partners(
            self.company_a,
            [self.duplicate_email],
            records=self.record_company_b,
            allowed_companies=[self.company_a, self.company_b],
        )
        self.assertEqual(found, [self.partner_company_b_duplicate])
