# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import SUPERUSER_ID, _, api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    other_journal_id = fields.Many2one(
        "account.journal", string="Paid By", domain=[("type", "in", ("bank", "cash"))]
    )
    other_move_id = fields.Many2one("account.move", string="Move in the other company")
    show_other_journal = fields.Boolean(default=False, invisible=True)

    @api.onchange("journal_id", "payment_type")
    def onchange_show_other_journal(self):
        for rec in self:
            res = (
                rec.journal_id.id == rec.company_id.due_fromto_payment_journal_id.id
                and rec.payment_type in ("outbound", "inbound")
                and rec.partner_type == "supplier"
            )
            # If False, reset the other journal
            if not res:
                rec.other_journal_id = False
            rec.show_other_journal = res

    def create_move_other_company(self):
        res = {}
        for rec in self:
            if rec.other_journal_id:
                other_company = rec.with_user(SUPERUSER_ID).other_journal_id.company_id
                # Update the existing move
                if rec.other_move_id:
                    # Cancel the entry
                    rec.other_move_id.with_user(SUPERUSER_ID).button_cancel()
                    # Delete the move lines
                    rec.other_move_id.with_user(SUPERUSER_ID).line_ids.unlink()
                    # Update the move with new lines
                    vals = rec._prepare_other_payment_values()
                    rec.other_move_id.with_user(SUPERUSER_ID).with_context(
                        force_company=other_company.id
                    ).write(vals)
                # or create a new one
                else:
                    # aml = self.env["account.move.line"].search(
                    #    [
                    #        ("account_id", "=", rec.company_id.due_to_account_id.id),
                    #        ("payment_id", "=", rec.id),
                    #    ]
                    # )
                    # aml.partner_id = other_company.partner_id.id
                    account_move = self.env["account.move"]
                    vals = rec._prepare_other_payment_values()
                    rec.other_move_id = (
                        account_move.with_user(SUPERUSER_ID)
                        .with_company(other_company)
                        .create(vals)
                    )
                # Post the move
                res = (
                    rec.other_move_id.with_user(SUPERUSER_ID)
                    .with_company(other_company)
                    .action_post()
                )
        return res

    def _prepare_other_payment_values(self):
        other_journal = self.with_user(SUPERUSER_ID).other_journal_id
        default_account_id = (
            other_journal.company_id.due_fromto_payment_journal_id.default_account_id.id
        )
        # Flip debit/credit for inbound
        if self.payment_type == "inbound":
            return {
                "partner_id": self.partner_id.id,
                "journal_id": other_journal.id,
                "state": "draft",
                "company_id": other_journal.company_id.id,
                "date": self.date,
                "ref": _("%s from %s" % (self.name, self.company_id.name)),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": default_account_id,
                            "partner_id": self.company_id.partner_id.id,
                            "credit": self.amount,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": other_journal.payment_debit_account_id.id,
                            "partner_id": self.partner_id.id,
                            "debit": self.amount,
                        },
                    ),
                ],
            }
        # Original Code
        else:
            return {
                "partner_id": self.partner_id.id,
                "journal_id": other_journal.id,
                "state": "draft",
                "company_id": other_journal.company_id.id,
                "date": self.date,
                "ref": _("%s from %s" % (self.name, self.company_id.name)),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": default_account_id,
                            "partner_id": self.company_id.partner_id.id,
                            "debit": self.amount,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": other_journal.payment_credit_account_id.id,
                            "partner_id": self.partner_id.id,
                            "credit": self.amount,
                        },
                    ),
                ],
            }

    def post(self):
        res = super().post()
        self.create_move_other_company()
        return res

    def action_validate_invoice_payment(self):
        res = super().action_validate_invoice_payment()
        self.create_move_other_company()
        return res
