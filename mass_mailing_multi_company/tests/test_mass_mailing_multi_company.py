# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestMassMailingMultiCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_model = cls.env["res.company"]
        cls.mailing_model = cls.env["mailing.mailing"]
        cls.mailing_list_model = cls.env["mailing.list"]
        cls.mailing_contact_model = cls.env["mailing.contact"]
        cls.mailing_subscription_model = cls.env["mailing.contact.subscription"]
        cls.mailing_contact_model.search([]).unlink()

        # Create test companies
        cls.company_1 = cls.company_model.create({"name": "Company 1"})
        cls.company_2 = cls.company_model.create({"name": "Company 2"})

        # Create test mailing list
        cls.mailing_list = cls.mailing_list_model.create(
            {
                "name": "Test Mailing List",
                "company_id": cls.company_1.id,
            }
        )

        cls.mailing_contact_1 = cls.mailing_contact_model.create(
            {
                "name": "Test Contact 1",
                "company_id": cls.company_1.id,
            }
        )
        cls.mailing_contact_2 = cls.mailing_contact_model.create(
            {
                "name": "Test Contact 2",
                "company_id": cls.company_1.id,
            }
        )
        cls.mailing_contact_3 = cls.mailing_contact_model.create(
            {
                "name": "Test Contact 3",
                "company_id": cls.company_2.id,
            }
        )

        # Create test mailing
        cls.mailing = cls.mailing_model.create(
            {
                "name": "Test Mailing",
                "subject": "Test",
                "mailing_domain": [("is_blacklisted", "=", False)],
                "company_id": cls.company_1.id,
                "mailing_model_id": cls.env.ref(
                    "mass_mailing.model_mailing_contact"
                ).id,
            }
        )

    def test_get_recipients(self):
        recipients = self.mailing._get_recipients()
        self.assertIn(self.mailing_contact_1.id, recipients)
        self.assertIn(self.mailing_contact_2.id, recipients)
        self.assertNotIn(self.mailing_contact_3.id, recipients)

        # Without company
        self.mailing.company_id = False
        recipients = self.mailing._get_recipients()
        self.assertIn(self.mailing_contact_1.id, recipients)
        self.assertIn(self.mailing_contact_2.id, recipients)
        self.assertIn(self.mailing_contact_3.id, recipients)

    def test_compute_total_with_company_id(self):
        # With company
        self.mailing._compute_total()
        self.assertEqual(self.mailing.total, 2)

        # Without company
        self.mailing.company_id = False
        self.mailing._compute_total()
        self.assertEqual(self.mailing.total, 3)
