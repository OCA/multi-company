# Copyright (C) 2026-TODAY NICO SOLUTIONS - ENGINEERING & IT (<https://www.nico-solutions.de>)
# @author Nils Coenen <nils.coenen@nico-solutions.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestResCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Test Company",
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        cls.role_owner = cls.env["res.company.representative.role"].create(
            {
                "name": "Owner",
            }
        )
        cls.env.user.lang = "en_US"
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                allowed_company_ids=[cls.company.id],
            )
        )

    def test_add_representative_to_company(self):
        self.env["res.company.representative"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "representative_role_id": self.role_owner.id,
                "sequence": 1,
            }
        )
        self.assertTrue(self.company.representatives)
        self.assertEqual(len(self.company.representatives), 1)
        self.assertEqual(
            self.company.representatives.partner_id,
            self.partner,
        )
        self.assertEqual(
            self.company.representatives.representative_role_id.name,
            "Owner",
        )

    def test_get_representatives(self):
        self.env["res.company.representative"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "representative_role_id": self.role_owner.id,
                "sequence": 1,
            }
        )
        result = self.company.get_representatives()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["partner"], self.partner.name)
        self.assertEqual(result[0]["role"], "Owner")

    def test_get_representatives_with_multiple_representatives(self):
        partner2 = self.env["res.partner"].create(
            {
                "name": "Test Partner 2",
            }
        )
        role_partner = self.env["res.company.representative.role"].create(
            {
                "name": "Partner",
            }
        )
        rep1 = self.env["res.company.representative"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "representative_role_id": self.role_owner.id,
                "sequence": 1,
            }
        )
        rep2 = self.env["res.company.representative"].create(
            {
                "company_id": self.company.id,
                "partner_id": partner2.id,
                "representative_role_id": role_partner.id,
                "sequence": 2,
            }
        )
        result = self.company.get_representatives()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["partner"], rep1.partner_id.name)
        self.assertEqual(result[0]["role"], "Owner")
        self.assertEqual(result[1]["partner"], rep2.partner_id.name)
        self.assertEqual(result[1]["role"], "Partner")

    def test_representative_sequence_is_per_company(self):
        company2 = self.env["res.company"].create(
            {
                "name": "Test Company 2",
            }
        )
        partner2 = self.env["res.partner"].create(
            {
                "name": "Test Partner 2",
            }
        )
        rep1 = self.env["res.company.representative"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "representative_role_id": self.role_owner.id,
            }
        )
        rep2 = self.env["res.company.representative"].create(
            {
                "company_id": company2.id,
                "partner_id": partner2.id,
                "representative_role_id": self.role_owner.id,
            }
        )
        self.assertEqual(rep1.sequence, 1)
        self.assertEqual(rep2.sequence, 1)

    def test_representative_sequence_is_assigned_automatically(self):
        partner2 = self.env["res.partner"].create(
            {
                "name": "Test Partner 2",
            }
        )
        rep1 = self.env["res.company.representative"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "representative_role_id": self.role_owner.id,
            }
        )
        rep2 = self.env["res.company.representative"].create(
            {
                "company_id": self.company.id,
                "partner_id": partner2.id,
                "representative_role_id": self.role_owner.id,
            }
        )
        self.assertEqual(rep1.sequence, 1)
        self.assertEqual(rep2.sequence, 2)
