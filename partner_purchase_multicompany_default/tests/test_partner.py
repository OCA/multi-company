# Copyright 2023 Moduon Team S.L.
# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo.tests.common import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class PartnerDefaultPurchaseCurrencyCase(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.currency_1 = cls.env.ref("base.EUR")

    def test_creation_propagation_currency(self):
        """Currencies are propagated on creation."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
                "property_purchase_currency_id": self.currency_1.id,
            }
        )
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        self.assertEqual(partner_cp2.property_purchase_currency_id, self.currency_1)

    def test_action_button_propagation_currency(self):
        """Currencies are propagated when user chooses to."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        # A partner created without accounts
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        self.assertNotEqual(partner.property_purchase_currency_id, self.currency_1)
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        # After writing accounts, they are still not propagated
        partner.write({"property_purchase_currency_id": self.currency_1.id})
        self.assertFalse(partner_cp2.property_purchase_currency_id)
        # Propagating payable account
        partner.propagate_multicompany_purchase_currency()
        self.assertEqual(partner_cp2.property_purchase_currency_id, self.currency_1)
