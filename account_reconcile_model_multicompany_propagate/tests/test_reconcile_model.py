# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)


from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPropagateReconcileModel(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.company = cls.company_data["company"]
        cls.partner_1 = cls.env["res.partner"].create(
            {"name": "partner_1", "company_id": cls.company.id}
        )
        cls.partner_2 = cls.env["res.partner"].create(
            {"name": "partner_2", "company_id": cls.company.id}
        )
        cls.category_8 = cls.env.ref("base.res_partner_category_8")
        cls.category_11 = cls.env.ref("base.res_partner_category_11")
        cls.rule_1 = cls.env["account.reconcile.model"].create(
            {
                "name": "Invoices Matching Rule Test",
                "sequence": "1000",
                "rule_type": "invoice_matching",
                "auto_reconcile": True,
                "to_check": True,
                "matching_order": "old_first",
                "match_text_location_label": True,
                "match_text_location_note": True,
                "match_text_location_reference": True,
                "match_nature": "both",
                "match_amount": "between",
                "match_amount_min": 1.0,
                "match_amount_max": 100000000.0,
                "match_label": "contains",
                "match_label_param": "label",
                "match_note": "contains",
                "match_note_param": "note",
                "match_transaction_type": "contains",
                "match_transaction_type_param": "transaction",
                "match_same_currency": True,
                "allow_payment_tolerance": True,
                "payment_tolerance_type": "percentage",
                "payment_tolerance_param": 1.0,
                "match_partner": True,
                "match_partner_ids": [(6, 0, (cls.partner_1 + cls.partner_2).ids)],
                "match_partner_category_ids": [
                    (6, 0, (cls.category_8 | cls.category_11).ids)
                ],
                "company_id": cls.company.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": cls.company_data[
                                "default_account_payable"
                            ].id,
                            "label": "label line",
                            "amount_string": "150",
                            "force_tax_included": True,
                            "tax_ids": [
                                (
                                    6,
                                    0,
                                    (
                                        cls.company_data["default_tax_sale"]
                                        | cls.company_data["default_tax_purchase"]
                                    ).ids,
                                )
                            ],
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": cls.company_data[
                                "default_account_revenue"
                            ].id,
                            "amount_string": "200",
                            "label": "label line 2",
                            "force_tax_included": False,
                        },
                    ),
                ],
                "partner_mapping_line_ids": [
                    (
                        0,
                        0,
                        {
                            "partner_id": cls.partner_1.id,
                            "payment_ref_regex": "payment ref regex",
                            "narration_regex": "narration regex",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "partner_id": cls.partner_2.id,
                            "payment_ref_regex": "payment ref regex 2",
                            "narration_regex": "narration regex 2",
                        },
                    ),
                ],
            }
        )

    def test_propagate_to_other_companies(self):
        self.rule_1.propagate_to_other_companies()
        rule_1_company_2 = self.env["account.reconcile.model"].search(
            [
                ("name", "=", self.rule_1.name),
                ("company_id", "=", self.company_data_2["company"].id),
            ]
        )
        self.assertTrue(rule_1_company_2)
        # Check propagate fields
        self.assertRecordValues(
            rule_1_company_2,
            [
                {
                    "rule_type": "invoice_matching",
                    "auto_reconcile": True,
                    "to_check": True,
                    "matching_order": "old_first",
                    "match_text_location_label": True,
                    "match_text_location_note": True,
                    "match_text_location_reference": True,
                    "match_nature": "both",
                    "match_amount": "between",
                    "match_amount_min": 1.0,
                    "match_amount_max": 100000000.0,
                    "match_label": "contains",
                    "match_label_param": "label",
                    "match_note": "contains",
                    "match_note_param": "note",
                    "match_transaction_type": "contains",
                    "match_transaction_type_param": "transaction",
                    "match_same_currency": True,
                    "allow_payment_tolerance": True,
                    "payment_tolerance_type": "percentage",
                    "payment_tolerance_param": 1.0,
                    "match_partner": True,
                    "match_partner_ids": (self.partner_1 + self.partner_2).ids,
                    "match_partner_category_ids": (
                        self.category_8 | self.category_11
                    ).ids,
                }
            ],
        )
        self.assertRecordValues(
            rule_1_company_2["line_ids"],
            [
                {
                    "account_id": self.company_data_2["default_account_payable"].id,
                    "amount_string": "150",
                    "label": "label line",
                    "force_tax_included": True,
                    "tax_ids": (
                        self.company_data_2["default_tax_sale"]
                        | self.company_data_2["default_tax_purchase"]
                    ).ids,
                },
                {
                    "account_id": self.company_data_2["default_account_revenue"].id,
                    "amount_string": "200",
                    "label": "label line 2",
                    "force_tax_included": False,
                    "tax_ids": [],
                },
            ],
        )
        self.assertRecordValues(
            rule_1_company_2["partner_mapping_line_ids"],
            [
                {
                    "partner_id": self.partner_1.id,
                    "payment_ref_regex": "payment ref regex",
                    "narration_regex": "narration regex",
                },
                {
                    "partner_id": self.partner_2.id,
                    "payment_ref_regex": "payment ref regex 2",
                    "narration_regex": "narration regex 2",
                },
            ],
        )
