# Copyright 2023 Moduon Team S.L.
# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo.tests.common import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class PartnerDefaultPricelistCase(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # A pricelist with same name on both companies
        cls.pricelist_a1 = cls.env["product.pricelist"].create(
            {
                "name": "A",
                "company_id": cls.company_data["company"].id,
            }
        )
        cls.pricelist_a2 = cls.env["product.pricelist"].create(
            {
                "name": "A",
                "company_id": cls.company_data_2["company"].id,
            }
        )
        # A pricelist available only on company 1
        cls.pricelist_b1 = cls.env["product.pricelist"].create(
            {
                "name": "B",
                "company_id": cls.company_data["company"].id,
            }
        )

    def test_creation_propagation_pricelist(self):
        """Pricelists are propagated on creation."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
                "property_product_pricelist": self.pricelist_a1.id,
            }
        )
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        self.assertEqual(partner_cp2.property_product_pricelist, self.pricelist_a2)

    def test_creation_no_propagation_pricelist(self):
        """Pricelists are not propagated on creation if they don't exist."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
                "property_product_pricelist": self.pricelist_b1.id,
            }
        )
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        # We expect pricelist set by default but not modified
        self.assertNotIn(partner_cp2.property_product_pricelist.name, ["A", "B"])

    def test_action_button_propagation_pricelist(self):
        """Pricelists are propagated when user chooses to."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        # A partner created without accounts
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        self.assertNotIn(partner.property_product_pricelist.name, ["A", "B"])
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        # After writing accounts, they are still not propagated
        partner.write(
            {
                "property_product_pricelist": self.pricelist_a1.id,
            }
        )
        self.assertNotEqual(
            partner_cp2.property_product_pricelist.name, self.pricelist_a1.name
        )
        # Propagating payable account
        partner.propagate_multicompany_product_pricelist()
        self.assertEqual(partner_cp2.property_product_pricelist, self.pricelist_a2)
