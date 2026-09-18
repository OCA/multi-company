# Copyright 2026 Tecnativa - Christian Ramos
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestResPartnerBankMultiCompany(common.TransactionCase):
    """Bank accounts must follow the multi-company visibility of their partner.

    Core stores ``res.partner.bank.company_id`` as a related field on
    ``partner_id.company_id``, which this module turns into a context dependent
    computed field. That stored value therefore collapses a multi-company
    partner down to a single company, making its bank accounts unusable from
    the rest of them. The module replaces the company consistency check with
    one based on ``company_ids``, and that is what is asserted here.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bank_model = cls.env["res.partner.bank"]
        cls.partner_model = cls.env["res.partner"].with_context(
            mail_create_nosubscribe=True,
        )
        cls.company_parent = cls.env["res.company"].create(
            [{"name": "Bank test parent company"}]
        )
        cls.company_child = cls.env["res.company"].create(
            [
                {
                    "name": "Bank test child company",
                    "parent_id": cls.company_parent.id,
                }
            ]
        )
        cls.company_other = cls.env["res.company"].create(
            [{"name": "Bank test unrelated company"}]
        )
        cls.partner = cls.partner_model.create(
            [
                {
                    "name": "Bank test partner",
                    "is_company": True,
                    "company_ids": [Command.set(cls.company_parent.ids)],
                }
            ]
        )
        cls.bank = cls.bank_model.create(
            [{"acc_number": "BANKTEST0001", "partner_id": cls.partner.id}]
        )

    def _set_partner_companies(self, companies):
        self.partner.company_ids = [Command.set(companies.ids)]
        # company_ids is a non stored related field, so drop what the previous
        # assertion may have cached for it
        self.bank.invalidate_recordset(["company_ids"])

    def _usable_from(self, company):
        """Emulate the company consistency check the ORM runs on the bank."""
        domain = self.bank_model._check_company_domain(company)
        return bool(self.bank.filtered_domain(domain))

    def test_check_company_auto_enabled(self):
        """The consistency check must actually run on create/write."""
        self.assertTrue(self.bank_model._check_company_auto)

    def test_company_ids_related_to_partner(self):
        """company_ids mirrors the partner and is not frozen like company_id."""
        self.assertEqual(self.bank.company_ids, self.company_parent)
        self._set_partner_companies(self.company_parent | self.company_other)
        self.assertEqual(
            self.bank.company_ids, self.company_parent | self.company_other
        )

    def test_domain_allows_shared_records(self):
        """The domain keeps records without companies visible to everyone.

        This is the only difference with the ``check_companies_domain_parent_of``
        helper shipped by the ORM, and the reason this module cannot use it.
        """
        domain = self.bank_model._check_company_domain(self.company_parent)
        self.assertIn(("company_ids", "=", False), domain)

    def test_domain_expands_company_hierarchy(self):
        """A child company resolves its parents through parent_path."""
        domain = self.bank_model._check_company_domain(self.company_child)
        companies = {
            company_id
            for leaf in domain
            if isinstance(leaf, tuple) and leaf[1] == "in"
            for company_id in leaf[2]
        }
        self.assertEqual(companies, {self.company_parent.id, self.company_child.id})

    def test_domain_without_companies(self):
        """No companies given means no restriction at all."""
        self.assertEqual(
            self.bank_model._check_company_domain(self.env["res.company"]), []
        )

    def test_domain_for_ui_is_hierarchical(self):
        """Domains built for the client side keep using ``parent_of``.

        ``fields.Many2one._description_domain`` feeds an ``unquote`` string
        instead of a recordset for ``check_company=True`` fields, and
        ``unquote`` subclasses ``str``.
        """
        domain = self.bank_model._check_company_domain("company_ids")
        self.assertIn(("company_ids", "parent_of", "company_ids"), domain)
        self.assertIn(("company_ids", "=", False), domain)

    def test_usable_from_own_company(self):
        self.assertTrue(self._usable_from(self.company_parent))

    def test_usable_from_child_company(self):
        """A branch may use the bank accounts of its parent company."""
        self.assertTrue(self._usable_from(self.company_child))

    def test_not_usable_from_parent_company(self):
        """Visibility must not leak upwards from a branch to its parent."""
        self._set_partner_companies(self.company_child)
        self.assertFalse(self._usable_from(self.company_parent))

    def test_not_usable_from_unrelated_company(self):
        self.assertFalse(self._usable_from(self.company_other))

    def test_usable_from_every_company_of_the_partner(self):
        """The case core cannot express with a single ``company_id``."""
        self._set_partner_companies(self.company_parent | self.company_other)
        self.assertTrue(self._usable_from(self.company_parent))
        self.assertTrue(self._usable_from(self.company_other))
        # ...and the hierarchy still applies to each of them
        self.assertTrue(self._usable_from(self.company_child))

    def test_partner_without_company_is_shared(self):
        """A partner with no company keeps its bank accounts shared."""
        self._set_partner_companies(self.env["res.company"])
        self.assertFalse(self.bank.company_ids)
        self.assertTrue(self._usable_from(self.company_parent))
        self.assertTrue(self._usable_from(self.company_child))
        self.assertTrue(self._usable_from(self.company_other))

    def test_domain_is_searchable(self):
        """The domain must also resolve in SQL, not only in memory."""
        domain = self.bank_model._check_company_domain(self.company_child)
        self.assertIn(self.bank, self.bank_model.search(domain))
        domain = self.bank_model._check_company_domain(self.company_other)
        self.assertNotIn(self.bank, self.bank_model.search(domain))
