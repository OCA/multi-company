# Copyright (C) 2026-TODAY NICO SOLUTIONS - ENGINEERING & IT (<https://www.nico-solutions.de>)
# @author Nils Coenen <nils.coenen@nico-solutions.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from psycopg2 import IntegrityError

from odoo.tests import TransactionCase


class TestResCompanyRepresentative(TransactionCase):
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
        cls.role = cls.env["res.company.representative.role"].create(
            {
                "name": "Owner",
            }
        )
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                allowed_company_ids=[cls.company.id],
            )
        )

    def test_create_representative(self):
        representative = self.env["res.company.representative"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "representative_role_id": self.role.id,
                "sequence": 1,
            }
        )
        self.assertEqual(representative.company_id, self.company)
        self.assertEqual(representative.partner_id, self.partner)
        self.assertEqual(
            representative.representative_role_id,
            self.role,
        )
        self.assertEqual(representative.sequence, 1)

    def test_create_representative_without_company_id(self):
        representative = self.env["res.company.representative"].create(
            {
                "partner_id": self.partner.id,
                "representative_role_id": self.role.id,
            }
        )
        self.assertEqual(
            representative.company_id,
            self.company,
        )

    def test_sequence_is_assigned_automatically(self):
        partner2 = self.env["res.partner"].create(
            {
                "name": "Test Partner 2",
            }
        )
        rep1 = self.env["res.company.representative"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "representative_role_id": self.role.id,
            }
        )
        rep2 = self.env["res.company.representative"].create(
            {
                "company_id": self.company.id,
                "partner_id": partner2.id,
                "representative_role_id": self.role.id,
            }
        )
        self.assertEqual(rep1.sequence, 1)
        self.assertEqual(rep2.sequence, 2)

    def test_sequence_is_per_company(self):
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
                "representative_role_id": self.role.id,
            }
        )
        rep2 = self.env["res.company.representative"].create(
            {
                "company_id": company2.id,
                "partner_id": partner2.id,
                "representative_role_id": self.role.id,
            }
        )
        self.assertEqual(rep1.sequence, 1)
        self.assertEqual(rep2.sequence, 1)

    def test_sequence_ordering(self):
        partner2 = self.env["res.partner"].create(
            {
                "name": "Test Partner 2",
            }
        )
        rep1 = self.env["res.company.representative"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "representative_role_id": self.role.id,
                "sequence": 1,
            }
        )
        rep2 = self.env["res.company.representative"].create(
            {
                "company_id": self.company.id,
                "partner_id": partner2.id,
                "representative_role_id": self.role.id,
                "sequence": 2,
            }
        )
        representatives = self.env["res.company.representative"].search(
            [("company_id", "=", self.company.id)],
            order="sequence asc",
        )
        self.assertEqual(representatives, rep1 | rep2)
        rep1.sequence = 3
        representatives = self.env["res.company.representative"].search(
            [("company_id", "=", self.company.id)],
            order="sequence asc",
        )
        self.assertEqual(representatives, rep2 | rep1)

    def test_duplicate_representative_is_not_allowed(self):
        self.env["res.company.representative"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "representative_role_id": self.role.id,
                "sequence": 1,
            }
        )
        logger = logging.getLogger("odoo.sql_db")
        previous_level = logger.level
        logger.setLevel(logging.CRITICAL)

        try:
            with self.assertRaises(IntegrityError), self.env.cr.savepoint():
                self.env["res.company.representative"].create(
                    {
                        "company_id": self.company.id,
                        "partner_id": self.partner.id,
                        "representative_role_id": self.role.id,
                        "sequence": 2,
                    }
                )
        finally:
            logger.setLevel(previous_level)
