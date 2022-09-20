# Copyright 2022 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"

    def _prepare_move_line_vals(self, payment_line, invoice, journal, company):
        vals_list = []
        vals1 = {}
        vals2 = {}
        vals = {
            "journal_id": journal.id,
            "move_id": invoice.id,
            "partner_id": invoice.partner_id.id,
            "company_id": company.id,
        }
        if invoice.move_type == "out_invoice":
            vals1 = {
                "account_id": journal.suspense_account_id.id,
                "debit": payment_line.amount_currency,
                "credit": 0.0,
            }
            vals2 = {
                "account_id": invoice.partner_id.with_company(
                    company.id
                ).property_account_receivable_id.id,
                "credit": payment_line.amount_currency,
                "debit": 0.0,
            }
        elif invoice.move_type == "in_invoice":
            vals1 = {
                "account_id": journal.suspense_account_id.id,
                "debit": 0.0,
                "credit": payment_line.amount_currency,
            }
            vals2 = {
                "account_id": invoice.partner_id.with_company(
                    company.id
                ).property_account_payable_id.id,
                "credit": 0.0,
                "debit": payment_line.amount_currency,
            }
        if vals1 and vals2:
            vals1.update(vals)
            vals2.update(vals)
            vals_list.extend((vals1, vals2))
        return vals_list

    def generate_move(self):
        super().generate_move()
        for bank_line in self.bank_line_ids:
            dest_company = (
                self.env["res.company"]
                .sudo()
                .search([("partner_id", "=", bank_line.partner_id.id)], limit=1)
            )
            if dest_company:
                for payment_line in bank_line.payment_line_ids:
                    orig_invoice = payment_line.move_line_id.move_id
                    if orig_invoice.auto_generated:
                        dest_invoice = orig_invoice.auto_invoice_id
                    else:
                        dest_invoice = self.env["account.move"].search(
                            [
                                ("auto_invoice_id", "=", orig_invoice.id),
                                ("company_id", "=", dest_company.id),
                            ],
                            limit=1,
                        )
                    if dest_invoice.payment_state != "paid":
                        dest_journal = self.env["account.journal"].search(
                            [
                                ("company_id", "=", dest_company.id),
                                ("type", "=", "bank"),
                                (
                                    "bank_account_id",
                                    "=",
                                    payment_line.partner_bank_id.id,
                                ),
                            ],
                            limit=1,
                        )
                        vals_list = self._prepare_move_line_vals(
                            payment_line, dest_invoice, dest_journal, dest_company
                        )
                        for vals in vals_list:
                            self.env["account.move.line"].with_context(
                                check_move_validity=False
                            ).create(vals)
                        lines_to_reconcile = dest_invoice.line_ids.filtered(
                            lambda line: line.account_internal_type
                            in ["receivable", "payable"]
                        )
                        lines_to_reconcile.reconcile()
