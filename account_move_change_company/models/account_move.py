# Copyright 2022 CreuBlanca
# Copyright 2024 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):

    _inherit = "account.move"

    company_id = fields.Many2one(
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain="[('id', 'in', allowed_company_ids)]",
    )
    allowed_company_ids = fields.Many2many(
        "res.company", compute="_compute_allowed_companies"
    )

    @api.depends("company_id")
    def _compute_allowed_companies(self):
        for record in self:
            record.allowed_company_ids = self.env.companies

    @api.depends("partner_id", "company_id")
    def _compute_invoice_payment_term_id(self):
        return super(
            AccountMove, self.with_company(self.company_id.id)
        )._compute_invoice_payment_term_id()

    @api.depends("bank_partner_id", "company_id")
    def _compute_partner_bank_id(self):
        return super(
            AccountMove, self.with_company(self.company_id.id)
        )._compute_partner_bank_id()

    @api.onchange("company_id")
    def _onchange_company(self):
        if self.journal_id.company_id == self.company_id:
            # This means we need to change nothing...
            return
        self = self.with_company(self.company_id.id)
        self.journal_id = (
            self.with_context(default_company_id=self.company_id.id)
            .with_company(self.company_id.id)
            ._search_default_journal()
        )
        self._inverse_journal_id()
        if not self.is_invoice():
            self.line_ids = [(5, 0, 0)]
            return

        for line in self.line_ids:
            line.company_id = self.company_id
            line._conditional_add_to_compute("account_id", lambda r: True)
            line._conditional_add_to_compute("tax_ids", lambda r: True)
