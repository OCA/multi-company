# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)


from odoo.tests.common import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class PartnerDefaultInvoiceTransmissionMethodCase(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.post_method = cls.env.ref("account_invoice_transmit_method.post")

    def test_creation_propagation_invoice_transmission_method(self):
        """Customer Invoice transmission methods are propagated on creation."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
                "customer_invoice_transmit_method_id": self.post_method.id,
                "supplier_invoice_transmit_method_id": self.post_method.id,
            }
        )
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        self.assertEqual(
            partner_cp2.customer_invoice_transmit_method_id, self.post_method
        )
        self.assertEqual(
            partner_cp2.supplier_invoice_transmit_method_id, self.post_method
        )
