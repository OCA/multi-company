# Copyright 2022 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"

    def _create_move_line_suspense_account(
        self, bank_line, bank_journal, move, dest_company
    ):
        vals = {
            "move_id": move.id,
            "company_id": dest_company.id,
            "account_id": bank_journal.suspense_account_id.id,
        }
        if self.payment_type == "outbound":
            vals["credit"] = 0.0
            vals["debit"] = bank_line.amount_currency
        else:
            vals["credit"] = bank_line.amount_currency
            vals["debit"] = 0.0
        return (
            self.env["account.move.line"]
            .with_context(check_move_validity=False)
            .create(vals)
        )

    def _prepare_move_line_vals(self, payment_line, dest_invoice, move, dest_company):
        vals = {
            "move_id": move.id,
            "partner_id": dest_invoice.commercial_partner_id.id,
            "company_id": dest_company.id,
            "name": dest_invoice.name,
        }
        if self.payment_type == "outbound":
            vals["account_id"] = dest_invoice.partner_id.with_company(
                dest_company.id
            ).property_account_receivable_id.id
            vals["credit"] = payment_line.amount_currency
            vals["debit"] = 0.0
        else:
            vals["account_id"] = dest_invoice.partner_id.with_company(
                dest_company.id
            ).property_account_payable_id.id
            vals["credit"] = 0.0
            vals["debit"] = payment_line.amount_currency
        return vals

    def _create_move_lines(self, bank_line, bank_journal, move, dest_company):
        move_lines = self._create_move_line_suspense_account(
            bank_line, bank_journal, move, dest_company
        )
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
            move_line_vals = self._prepare_move_line_vals(
                payment_line, dest_invoice, move, dest_company
            )
            move_lines |= (
                self.env["account.move.line"]
                .with_context(check_move_validity=False)
                .create(move_line_vals)
            )
        return move_lines

    def _prepare_move_vals(self, dest_company, bank_journal, bank_line):
        vals = {
            "journal_id": bank_journal.id,
            "company_id": dest_company.id,
            "ref": bank_line.communication,
        }
        return vals

    def _create_move(self, dest_company, bank_journal, bank_line):
        vals = self._prepare_move_vals(dest_company, bank_journal, bank_line)
        return self.env["account.move"].create(vals)

    def _reconcile_lines(self, move_lines):
        for line in move_lines.filtered(
            lambda line: line.account_internal_type in ["receivable", "payable"]
        ):
            lines_to_reconcile = line
            dest_invoice_line = self.env["account.move.line"].search(
                [
                    ("account_internal_type", "in", ["receivable", "payable"]),
                    ("move_name", "=", line.name),
                ],
                limit=1,
            )
            lines_to_reconcile |= dest_invoice_line
            lines_to_reconcile.reconcile()
        return True

    def generate_move(self):
        super().generate_move()
        for bank_line in self.bank_line_ids:
            dest_company = (
                self.env["res.company"]
                .sudo()
                .search([("partner_id", "=", bank_line.partner_id.id)], limit=1)
            )
            if dest_company:
                bank_journal = self.env["account.journal"].search(
                    [
                        ("company_id", "=", dest_company.id),
                        ("type", "=", "bank"),
                        (
                            "bank_account_id.sanitized_acc_number",
                            "=",
                            bank_line.partner_bank_id.sanitized_acc_number,
                        ),
                    ],
                    limit=1,
                )
                move = self._create_move(dest_company, bank_journal, bank_line)
                move_lines = self._create_move_lines(
                    bank_line, bank_journal, move, dest_company
                )
                move.action_post()
                self._reconcile_lines(move_lines)
