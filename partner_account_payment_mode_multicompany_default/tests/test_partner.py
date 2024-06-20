# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)


from odoo.tests.common import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class PartnerDefaultPaymentModeCase(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.payment_mode_model = cls.env["account.payment.mode"]
        cls.manual_out = cls.env.ref("account.account_payment_method_manual_out")
        cls.manual_out.bank_account_required = True
        cls.supplier_payment_mode = cls.payment_mode_model.create(
            {
                "name": "Suppliers Bank 1",
                "bank_account_link": "variable",
                "payment_method_id": cls.manual_out.id,
                "show_bank_account_from_journal": True,
                "company_id": cls.company_data["company"].id,
            }
        )

        cls.supplier_payment_mode_c2 = cls.payment_mode_model.create(
            {
                "name": "Suppliers Bank 1",
                "bank_account_link": "variable",
                "payment_method_id": cls.manual_out.id,
                "company_id": cls.company_data_2["company"].id,
            }
        )

    def test_creation_propagation_account_payment_mode(self):
        """Accounts payment modes are propagated on creation."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        partner = env["res.partner"].create(
            {
                "name": "Test Partner",
                "supplier_payment_mode_id": self.supplier_payment_mode.id,
            }
        )
        partner_cp2 = partner.with_company(self.company_data_2["company"].id)
        self.assertEqual(
            partner_cp2.supplier_payment_mode_id, self.supplier_payment_mode_c2
        )
