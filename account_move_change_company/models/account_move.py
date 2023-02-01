# Copyright 2022 CreuBlanca
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

    @api.onchange("company_id")
    def _onchange_company(self):
        if self.journal_id.company_id == self.company_id:
            # This means we need to change nothing...
            return
        move_type = self.move_type
        if move_type in self.get_sale_types(include_receipts=True):
            journal_types = ["sale"]
        elif move_type in self.get_purchase_types(include_receipts=True):
            journal_types = ["purchase"]
        else:
            journal_types = self._context.get("default_move_journal_types", ["general"])
        self.journal_id = self.with_context(
            default_company_id=self.company_id.id
        )._search_default_journal(journal_types)
        if not self.is_invoice():
            self.line_ids = [(5, 0, 0)]
            return
        # Forcing recalculation of change of partner
        self._onchange_partner_id()
        for line in self.invoice_line_ids:
            line.account_id = line._get_computed_account()
            taxes = line._get_computed_taxes()
            if taxes and line.move_id.fiscal_position_id:
                taxes = line.move_id.fiscal_position_id.map_tax(
                    taxes, partner=line.partner_id
                )
            line.tax_ids = taxes
        self.line_ids.update({"company_id": self.company_id.id})
        self._onchange_recompute_dynamic_lines()
