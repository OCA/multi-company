# Copyright 2023 Moduon Team S.L.
# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo.tests.common import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class PartnerDefaultCarrierCase(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # A carrier with same name on both companies
        product_a1 = cls.env.ref("delivery.product_product_delivery_poste")
        product_a2 = product_a1.copy()
        product_b1 = product_a1.copy()
        cls.carrier_a1 = cls.env["delivery.carrier"].create(
            {
                "name": "A",
                "company_id": cls.company_data["company"].id,
                "product_id": product_a1.id,
            }
        )
        cls.carrier_a2 = cls.env["delivery.carrier"].create(
            {
                "name": "A",
                "company_id": cls.company_data_2["company"].id,
                "product_id": product_a2.id,
            }
        )
        # A carrier available only on company 1
        cls.carrier_b1 = cls.env["delivery.carrier"].create(
            {
                "name": "B",
                "company_id": cls.company_data["company"].id,
                "product_id": product_b1.id,
            }
        )

    def test_creation_propagation_carrier(self):
        """Carriers are propagated on creation."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
                "property_delivery_carrier_id": self.carrier_a1.id,
            }
        )
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        self.assertEqual(partner_cp2.property_delivery_carrier_id, self.carrier_a2)

    def test_creation_no_propagation_carrier(self):
        """Carriers are not propagated on creation if they don't exist."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
                "property_delivery_carrier_id": self.carrier_b1.id,
            }
        )
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        # We expect carrier set by default but not modified
        self.assertNotIn(partner_cp2.property_delivery_carrier_id.name, ["A", "B"])

    def test_action_button_propagation_carrier(self):
        """Carriers are propagated when user chooses to."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        # A partner created without carrier
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        self.assertNotIn(partner.property_delivery_carrier_id.name, ["A", "B"])
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        # After writing carrier, it is still not propagated
        partner.write(
            {
                "property_delivery_carrier_id": self.carrier_a1.id,
            }
        )
        self.assertNotEqual(
            partner_cp2.property_delivery_carrier_id.name, self.carrier_a1.name
        )
        # Propagating carrier
        partner.propagate_multicompany_delivery_carrier()
        self.assertEqual(partner_cp2.property_delivery_carrier_id, self.carrier_a2)
