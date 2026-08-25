# Copyright 2023 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import Command
from odoo.tests import Form

from odoo.addons.account_invoice_inter_company.tests.test_inter_company_invoice import (
    TestAccountInvoiceInterCompanyBase,
)


class TestPurchaseSaleNoteIntercompany(TestAccountInvoiceInterCompanyBase):
    @classmethod
    def _configure_user(cls, user):
        for xml in [
            "account.group_account_manager",
            "base.group_partner_manager",
            "sales_team.group_sale_manager",
            "purchase.group_purchase_manager",
        ]:
            user.groups_id |= cls.env.ref(xml)

    @classmethod
    def _create_purchase_order(cls, partner, products=None):
        if not products:
            products = [None]

        po = Form(cls.env["purchase.order"])
        po.company_id = cls.company_a
        po.partner_id = partner

        cls.product.invoice_policy = "order"

        for product in products:
            with po.order_line.new() as line_form:
                line_form.product_id = product or cls.product
                line_form.product_qty = 3.0
                line_form.price_unit = 450.0
        return po.save()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # no job: avoid issue if account_invoice_inter_company_queued is installed
        cls.env = cls.env(
            context=dict(
                cls.env.context, tracking_disable=True, test_queue_job_no_delay=True
            )
        )

        cls.product = cls.product_consultant_multi_company
        cls.service_product_2 = cls.env["product.product"].create(
            {
                "name": "Service Product 2",
                "type": "service",
            }
        )
        # if product_multi_company is installed
        if "company_ids" in cls.env["product.template"]._fields:
            # We have to do that because the default method added a company
            cls.service_product_2.company_ids = False

        if "company_ids" in cls.env["res.partner"]._fields:
            # Intercompany contacts should not have a company set
            cls.partner_company_a.company_ids = False
            cls.partner_company_b.company_ids = False

        # Configure Company B (the supplier)
        cls.company_b.so_from_po = True
        cls.company_b.sale_auto_validation = 1

        cls.intercompany_sale_user_id = cls.user_company_b.copy()
        cls.intercompany_sale_user_id.company_ids |= cls.company_a
        cls.company_b.intercompany_sale_user_id = cls.intercompany_sale_user_id

        # Configure User
        cls._configure_user(cls.user_company_a)
        cls._configure_user(cls.user_company_b)
        cls._configure_user(cls.intercompany_sale_user_id)

        # Create purchase order
        cls.purchase_company_a = cls._create_purchase_order(cls.partner_company_b)
        cls.purchase_company_a.order_line[0].note = "Some details"

        # Create account
        income_account = cls.env["account.account"].create(
            {
                "name": "test_account_income",
                "code": "987",
                "account_type": "income",
                "company_ids": [Command.set([cls.company_b.id])],
            }
        )
        expense_account = cls.env["account.account"].create(
            {
                "name": "test account_expenses",
                "code": "765",
                "account_type": "expense",
                "reconcile": True,
                "company_ids": [Command.set([cls.company_a.id])],
            }
        )
        # Create journal
        cls.env["account.journal"].create(
            {
                "name": "Customer Invoices - Test",
                "code": "TEST1",
                "type": "sale",
                "company_id": cls.company_b.id,
                "default_account_id": income_account.id,
            }
        )
        cls.env["account.journal"].create(
            {
                "name": "Vendor Bills - Test",
                "code": "TEST2",
                "type": "purchase",
                "company_id": cls.company_a.id,
                "default_account_id": expense_account.id,
            }
        )

    def _approve_po(self, purchase_to_approve=None):
        """Confirm the PO in company A and return the related sale of Company B"""
        if not purchase_to_approve:
            purchase_to_approve = self.purchase_company_a
        partner_company = purchase_to_approve.company_id.partner_id.company_id
        assert not partner_company, (
            "The partner should not have a company set, otherwise the "
            "intercompany_sale_order_id will not be computed properly. Current "
            f"partner company_id: {partner_company.name}"
        )
        purchase_to_approve.with_user(self.user_company_a).button_approve()
        return (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", purchase_to_approve.id)])
        )

    def test_propagated_note_intercompany(self):
        sale = self._approve_po()
        self.assertEqual(sale.order_line[0].note, "Some details")
