# Copyright 2023 Moduon Team S.L.
# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)


from odoo.tests.common import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class PartnerDefaultAccountsCase(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # An payable account with same code on both companies
        cls.account_payable_a1 = cls.env["account.account"].create(
            {
                "name": "Payable A1",
                "code": "PAY.A",
                "account_type": "liability_payable",
                "company_id": cls.company_data["company"].id,
            }
        )
        cls.account_payable_a2 = cls.env["account.account"].create(
            {
                "name": "Payable A2",
                "code": "PAY.A",
                "account_type": "liability_payable",
                "company_id": cls.company_data_2["company"].id,
            }
        )
        # An payable account available only on company 1
        cls.account_payable_b1 = cls.env["account.account"].create(
            {
                "name": "Payable B1",
                "code": "PAY.B",
                "account_type": "liability_payable",
                "company_id": cls.company_data["company"].id,
            }
        )
        # An receivable account with same code on both companies
        cls.account_receivable_a1 = cls.env["account.account"].create(
            {
                "name": "Receivable A1",
                "code": "REC.A",
                "account_type": "asset_receivable",
                "company_id": cls.company_data["company"].id,
            }
        )
        cls.account_receivable_a2 = cls.env["account.account"].create(
            {
                "name": "Receivable A2",
                "code": "REC.A",
                "account_type": "asset_receivable",
                "company_id": cls.company_data_2["company"].id,
            }
        )
        # An receivable account available only on company 1
        cls.account_receivable_b1 = cls.env["account.account"].create(
            {
                "name": "Receivable B1",
                "code": "REC.B",
                "account_type": "asset_receivable",
                "company_id": cls.company_data["company"].id,
            }
        )

        cls.fiscal_position_a1 = cls.env["account.fiscal.position"].create(
            {
                "name": "Fiscal Pos A",
                "company_id": cls.company_data["company"].id,
            }
        )
        cls.fiscal_position_a2 = cls.env["account.fiscal.position"].create(
            {
                "name": "Fiscal Pos A",
                "company_id": cls.company_data_2["company"].id,
            }
        )
        cls.fiscal_position_b1 = cls.env["account.fiscal.position"].create(
            {
                "name": "Fiscal Pos B",
                "company_id": cls.company_data["company"].id,
            }
        )
        cls.payment_term_a1 = cls.env["account.payment.term"].create(
            {
                "name": "Payment Term A",
                "company_id": cls.company_data["company"].id,
            }
        )
        cls.payment_term_a2 = cls.env["account.payment.term"].create(
            {
                "name": "Payment Term A",
                "company_id": cls.company_data_2["company"].id,
            }
        )
        cls.payment_term_b1 = cls.env["account.payment.term"].create(
            {
                "name": "Payment Term B",
                "company_id": cls.company_data["company"].id,
            }
        )
        cls.payment_term_c = cls.env["account.payment.term"].create(
            {
                "name": "Payment Term A",
                "company_id": False,
            }
        )
        cls.supplier_payment_term_a1 = cls.env["account.payment.term"].create(
            {
                "name": "Supplier Payment Term A",
                "company_id": cls.company_data["company"].id,
            }
        )
        cls.supplier_payment_term_a2 = cls.env["account.payment.term"].create(
            {
                "name": "Supplier Payment Term A",
                "company_id": cls.company_data_2["company"].id,
            }
        )
        cls.supplier_payment_term_b1 = cls.env["account.payment.term"].create(
            {
                "name": "Supplier Payment Term B",
                "company_id": cls.company_data["company"].id,
            }
        )
        cls.supplier_payment_term_c = cls.env["account.payment.term"].create(
            {
                "name": "Supplier Payment Term A",
                "company_id": False,
            }
        )

    def test_creation_propagation_accounts(self):
        """Accounts are propagated on creation."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
                "property_account_payable_id": self.account_payable_a1.id,
                "property_account_receivable_id": self.account_receivable_a1.id,
            }
        )
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        self.assertEqual(
            partner_cp2.property_account_payable_id, self.account_payable_a2
        )
        self.assertEqual(
            partner_cp2.property_account_receivable_id, self.account_receivable_a2
        )

    def test_creation_propagation_fiscal_position(self):
        """Fiscal position are propagated on creation."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
                "property_account_position_id": self.fiscal_position_a1.id,
            }
        )
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        self.assertEqual(
            partner_cp2.property_account_position_id, self.fiscal_position_a2
        )

    def test_creation_propagation_payment_terms(self):
        """Fiscal position are propagated on creation."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
                "property_payment_term_id": self.payment_term_a1.id,
                "property_supplier_payment_term_id": self.supplier_payment_term_a1.id,
            }
        )
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        self.assertEqual(partner_cp2.property_payment_term_id, self.payment_term_a2)
        self.assertEqual(
            partner_cp2.property_supplier_payment_term_id, self.supplier_payment_term_a2
        )

    def test_creation_propagation_payment_terms_shared(self):
        """Shared payment terms are propagated on creation."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
                "property_payment_term_id": self.payment_term_c.id,
                "property_supplier_payment_term_id": self.supplier_payment_term_c.id,
            }
        )
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        self.assertEqual(partner_cp2.property_payment_term_id, self.payment_term_c)
        self.assertEqual(
            partner_cp2.property_supplier_payment_term_id, self.supplier_payment_term_c
        )

    def test_creation_no_propagation_accounts(self):
        """Accounts are not propagated on creation if they don't exist."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
                "property_account_payable_id": self.account_payable_b1.id,
                "property_account_receivable_id": self.account_receivable_b1.id,
            }
        )
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        test_codes = ["PAY.A", "PAY.B", "REC.A"]
        # We expect account set by default but not modified
        self.assertNotIn(partner_cp2.property_account_payable_id.code, test_codes)
        self.assertNotIn(partner_cp2.property_account_receivable_id.code, test_codes)

    def test_creation_no_propagation_fiscal_position(self):
        """Fiscal position are not propagated on creation if they don't exist."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
                "property_account_position_id": self.fiscal_position_b1.id,
            }
        )
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        test_codes = ["PAY.A", "PAY.B", "REC.A"]
        # We expect account set by default but not modified
        self.assertNotIn(partner_cp2.property_account_payable_id.code, test_codes)
        self.assertNotIn(partner_cp2.property_account_receivable_id.code, test_codes)
        self.assertNotEqual(
            partner_cp2.property_account_position_id.name, "Fiscal Pos B"
        )

    def test_creation_no_propagation_payment_terms(self):
        """Payment terms are not propagated on creation if they don't exist."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
                "property_payment_term_id": self.payment_term_b1.id,
                "property_supplier_payment_term_id": self.supplier_payment_term_b1.id,
            }
        )
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        # We expect payment terms set by default but not modified
        self.assertFalse(partner_cp2.property_payment_term_id)
        self.assertFalse(partner_cp2.property_supplier_payment_term_id)

    def test_action_button_propagation_accounts(self):
        """Accounts are propagated when user chooses to."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        # A partner created without accounts
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        test_codes = ["PAY.A", "PAY.B", "REC.A"]
        self.assertNotIn(partner.property_account_payable_id.code, test_codes)
        self.assertNotIn(partner.property_account_receivable_id.code, test_codes)
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        # After writing accounts, they are still not propagated
        partner.write(
            {
                "property_account_payable_id": self.account_payable_a1.id,
                "property_account_receivable_id": self.account_receivable_a1.id,
            }
        )
        self.assertNotEqual(
            partner_cp2.property_account_payable_id.code, self.account_payable_a1.code
        )
        self.assertNotIn(
            partner_cp2.property_account_receivable_id.code,
            self.account_receivable_a1.code,
        )
        # Propagating payable account
        partner.propagate_multicompany_account_payable()
        self.assertEqual(
            partner_cp2.property_account_payable_id, self.account_payable_a2
        )
        self.assertNotIn(
            partner_cp2.property_account_receivable_id.code,
            self.account_receivable_a1.code,
        )
        # Propagating receivable account
        partner.propagate_multicompany_account_receivable()
        self.assertEqual(
            partner_cp2.property_account_payable_id, self.account_payable_a2
        )
        self.assertEqual(
            partner_cp2.property_account_receivable_id, self.account_receivable_a2
        )

    def test_action_button_propagation_fiscal_position(self):
        """Fiscal position are propagated when user chooses to."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        # A partner created without accounts
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        self.assertNotEqual(partner.property_account_position_id.name, "Fiscal Pos A")
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        # After writing accounts, it is still not propagated
        partner.write(
            {
                "property_account_position_id": self.fiscal_position_a1.id,
            }
        )
        self.assertNotIn(
            partner_cp2.property_account_receivable_id.code,
            self.account_receivable_a1.code,
        )
        self.assertNotEqual(
            partner_cp2.property_account_position_id.name, "Fiscal Pos A"
        )
        # Propagating fiscal position
        partner.propagate_multicompany_account_position()
        self.assertEqual(
            partner_cp2.property_account_position_id, self.fiscal_position_a2
        )

    def test_action_button_propagation_payment_terms(self):
        """Payment terms are propagated when user chooses to."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        # A partner created without accounts
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        self.assertNotEqual(partner.property_account_position_id.name, "Fiscal Pos A")
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        # After writing accounts, it is still not propagated
        partner.write(
            {
                "property_payment_term_id": self.payment_term_a1.id,
                "property_supplier_payment_term_id": self.supplier_payment_term_a1.id,
            }
        )
        self.assertFalse(
            partner_cp2.property_payment_term_id,
        )
        self.assertFalse(
            partner_cp2.property_supplier_payment_term_id,
        )
        # Propagating payment terms
        partner.propagate_multicompany_payment_term_id()
        self.assertEqual(partner_cp2.property_payment_term_id, self.payment_term_a2)
        partner.propagate_multicompany_supplier_payment_term_id()
        self.assertEqual(
            partner_cp2.property_supplier_payment_term_id, self.supplier_payment_term_a2
        )

    def test_action_button_propagation_payment_terms_shared(self):
        """Payment terms are propagated when user chooses to."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        # A partner created without accounts
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        self.assertFalse(partner.property_payment_term_id)
        self.assertFalse(partner.property_payment_term_id)
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        # After writing accounts, it is still not propagated
        partner.write(
            {
                "property_payment_term_id": self.payment_term_a1.id,
                "property_supplier_payment_term_id": self.supplier_payment_term_a1.id,
            }
        )
        self.assertFalse(
            partner_cp2.property_payment_term_id,
        )
        self.assertFalse(
            partner_cp2.property_supplier_payment_term_id,
        )
        # Propagating payment terms
        partner.propagate_multicompany_payment_term_id()
        self.assertEqual(partner_cp2.property_payment_term_id, self.payment_term_a2)
        partner.propagate_multicompany_supplier_payment_term_id()
        self.assertEqual(
            partner_cp2.property_supplier_payment_term_id, self.supplier_payment_term_a2
        )
