# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountInvoiceConsolidation(models.Model):
    _name = "account.invoice.consolidated"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Invoice Consolidation"

    @api.depends("invoice_ids", "invoice_id", "payment_ids")
    def compute_amount(self):
        amount_untaxed = 0.0
        amount_tax = 0.0
        residual = 0.0
        for consolidated_inv in self.sudo():
            invoice_ids = (
                consolidated_inv.invoice_ids.sudo()
                .search([("consolidated_by_id", "=", consolidated_inv.id)])
                .ids
            )
            if invoice_ids:
                self.env.cr.execute(
                    """
                    SELECT
                        sum(amount_untaxed) as amount_untaxed,
                        sum(amount_tax) as amount_tax,
                        sum(amount_residual) as amount_residual
                    FROM
                        account_move
                    WHERE
                        id in %s
                """,
                    (tuple(invoice_ids),),
                )
                vals = self.env.cr.dictfetchall()
                amount_untaxed += vals[0]["amount_untaxed"]
                amount_tax += vals[0]["amount_tax"]
                residual += vals[0]["amount_residual"]
            consolidated_inv.amount_untaxed = amount_untaxed
            consolidated_inv.amount_tax = amount_tax
            consolidated_inv.residual = residual
            consolidated_inv.amount_total = amount_untaxed + amount_tax

    name = fields.Char(readonly=True, default="Draft")
    date_from = fields.Date(
        required=True, readonly=True, states={"draft": [("readonly", False)]}
    )
    date_to = fields.Date(
        required=True, readonly=True, states={"draft": [("readonly", False)]}
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        tracking=True,
        default=lambda self: self.env.user.company_id,
    )
    partner_id = fields.Many2one(
        "res.partner",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        tracking=True,
    )
    currency_id = fields.Many2one(related="company_id.currency_id", readonly=True)
    amount_untaxed = fields.Monetary(
        compute="_compute_amount", tracking=True, store=True
    )
    amount_tax = fields.Monetary(compute="_compute_amount", tracking=True, store=True)
    amount_total = fields.Monetary(compute="_compute_amount", tracking=True, store=True)
    residual = fields.Monetary(
        compute="_compute_amount", string="Amount Due", tracking=True, store=True
    )
    amount_currency = fields.Monetary()
    invoice_id = fields.Many2one(
        "account.move",
        string="Consolidated Invoice",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    invoice_ids = fields.One2many("account.move", "consolidated_by_id")
    payment_ids = fields.One2many(
        "account.payment",
        "consolidation_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        [("draft", "Draft"), ("invoice", "Invoice"), ("done", "Done")],
        default="draft",
        readonly=True,
        tracking=True,
    )

    invoice_line_ids = fields.One2many(
        "account.move.line", "consolidated_by_id", string="Invoice Line Ids"
    )

    @api.constrains("name")
    def _check_name_duplication(self):
        for inv in self:
            if inv.name != "Draft":
                if self.search_count([("name", "=", inv.name), ("id", "!=", inv.id)]):
                    raise ValidationError(
                        _("Consolidated Invoice Number must be unique!")
                    )

    @api.constrains("partner_id", "date_from", "date_to")
    def _check_date_validation(self):
        for inv in self:
            if inv.date_from > inv.date_to:
                raise ValidationError(_("End Date should be greater than Start Date!"))
            if (
                inv.search_count(
                    [
                        ("state", "=", "draft"),
                        ("partner_id", "=", inv.partner_id.id),
                        "|",
                        "|",
                        "&",
                        ("date_from", "<=", inv.date_from),
                        ("date_to", ">=", inv.date_from),
                        "&",
                        ("date_from", "<=", inv.date_to),
                        ("date_to", ">=", inv.date_to),
                        "&",
                        ("date_from", "<=", inv.date_from),
                        ("date_to", ">=", inv.date_to),
                    ]
                )
                > 1
            ):
                raise ValidationError(
                    _(
                        "Draft Consolidated Invoice exists for selected "
                        "Customer/Date Range.\n Please add the invoice there."
                    )
                )

    def get_invoices(self):
        if (
            not self.partner_id
            or self.invoice_ids
            and self.partner_id
            and self.invoice_ids[0].partner_id != self.partner_id
        ):
            self.invoice_ids = False
        if self.date_from and self.date_to and self.partner_id:
            inv_rec = (
                self.env["account.move"]
                .sudo()
                .search(
                    [
                        ("partner_id", "=", self.partner_id.id),
                        ("invoice_date", ">=", self.date_from),
                        ("invoice_date", "<=", self.date_to),
                        ("state", "=", "posted"),
                        ("payment_state", "!=", "paid"),
                        ("move_type", "=", "out_invoice"),
                    ]
                )
            )
            if inv_rec:
                for inv in inv_rec:
                    query = """UPDATE
                                    account_move SET
                                    consolidated_by_id = %s
                                WHERE id=%s
                            """
                    self.env.cr.execute(query, [self.id, inv.id])
                    for _inv_line in inv:
                        query = """UPDATE account_move_line \
                        SET consolidated_by_id = %s WHERE id=%s"""
                        self.env.cr.execute(query, [self.id, inv.id])
            self.sudo().invoice_ids = (
                self.env["account.move"]
                .sudo()
                .search([("consolidated_by_id", "=", self.id)])
                .ids
            )
            self.sudo().invoice_line_ids = (
                self.env["account.move.line"]
                .sudo()
                .search([("consolidated_by_id", "=", self.id)])
                .ids
            )

    def get_invoice_price(self):
        self.get_invoices()
        self.compute_amount()
        if self.state != "invoice":
            self.state = "invoice"

    def action_confirm_invoice(self):
        for rec in self.sudo():
            if not rec.invoice_ids:
                raise ValidationError(_("Add some invoices to proceed further."))
            # Validation to check Intercompany Payment Configuration
            company_ids = rec.company_id
            company_ids |= rec.invoice_ids.mapped("company_id")
            for company in company_ids:
                if (
                    not company.due_from_account_id
                    or not company.due_to_account_id
                    or not company.due_fromto_payment_journal_id
                ):
                    raise ValidationError(
                        _(
                            "Intercompany Payment Configuration is missing for"
                            " %s." % (company.display_name)
                        )
                    )
            invoice_consolidated_seq = self.env["ir.sequence"].next_by_code(
                "consolidated.invoice"
            )
            if invoice_consolidated_seq:
                rec.write({"name": invoice_consolidated_seq})

            inv_vals = {
                "move_type": "out_invoice",
                "payment_reference": rec.name,
                "partner_id": rec.partner_id.id,
                "invoice_payment_term_id": rec.partner_id.property_payment_term_id.id,
                "company_id": rec.company_id.id,
            }
            line_ids = self.sudo().prepare_consolidated_invoice_line_values() or []
            for invoice in rec.sudo().invoice_ids:
                payment = (
                    self.env["account.payment"]
                    .sudo()
                    .create(self.sudo().prepare_payment_values(invoice))
                )
                # Validate the payment to reconcile the invoice
                payment.sudo().action_post()
                for payment_rec in payment.move_id.line_ids:
                    if payment_rec.account_id == payment.destination_account_id:
                        invoice.js_assign_outstanding_line(payment_rec.id)

            inv_vals.update({"invoice_line_ids": line_ids})
            # Create and validate the consolidated invoice
            invoice_id = (
                self.env["account.move"]
                .sudo()
                .with_context(company_id=rec.company_id.id)
                .create(inv_vals)
            )
            if invoice_id.invoice_line_ids:
                invoice_id.action_post()
            rec.compute_amount()
            rec.write({"invoice_id": invoice_id.id, "state": "done"})

    def unlink(self):
        for inv in self:
            if inv.state == "done":
                raise ValidationError(
                    _("You cannot delete a finished consolidated invoice.")
                )
            for invoice_id in inv.sudo().invoice_ids:
                invoice = self.env["account.move"].sudo().browse(invoice_id.id)
                invoice.consolidated_by_id = False
            for invoice_line_id in inv.sudo().invoice_line_ids:
                invoice_line = (
                    self.env["account.move.line"].sudo().browse(invoice_line_id.id)
                )
                invoice_line.consolidated_by_id = False
        return super().unlink()

    def get_tax(self, tax_ids):
        tax_obj = self.env["account.tax"]
        tax_list = []
        for tax_id in tax_ids:
            tax = tax_obj.sudo().search(
                [
                    ("name", "=", tax_id.name),
                    ("company_id", "=", self.company_id.id),
                    ("type_tax_use", "=", tax_id.type_tax_use),
                ],
                limit=1,
            )
            tax_list.append(tax.id)
        return tax_list

    def prepare_consolidated_invoice_line_values(self):
        res = []
        for invoice_id in self.sudo().invoice_ids:
            for line_id in invoice_id.sudo().invoice_line_ids:
                rec = (
                    0,
                    0,
                    {
                        "name": line_id.name + " - " + line_id.company_id.name,
                        "sequence": line_id.sequence,
                        "ref": line_id.move_id.name,
                        "account_id": self.company_id.due_to_account_id.id,
                        "price_unit": line_id.price_unit,
                        "quantity": line_id.quantity,
                        "discount": line_id.discount,
                        "product_uom_id": line_id.product_uom_id.id,
                        "tax_base_amount": line_id.tax_base_amount,
                        "tax_ids": [(6, 0, self.get_tax(line_id.tax_ids))],
                        "display_type": line_id.display_type,
                        "price_subtotal": line_id.price_subtotal,
                    },
                )
                res.append(rec)
        return res

    def prepare_payment_values(self, invoice):
        journal_id = invoice.company_id.due_fromto_payment_journal_id
        res = {
            "partner_id": self.company_id.partner_id.id,
            "partner_type": "customer",
            "amount": invoice.amount_residual,
            "journal_id": journal_id.id,
            "payment_type": "inbound",
            "payment_method_id": journal_id.inbound_payment_method_ids[0].id,
            "date": fields.Datetime.now(),
            "consolidation_id": self.id,
            "company_id": invoice.company_id.id,
            "reconciled_invoice_ids": [(4, invoice.id, None)],
            "move_type": "entry",
        }
        return res
