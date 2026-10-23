# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_compare
from odoo.tools.misc import clean_context

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    auto_generated = fields.Boolean(
        "Auto Generated Document", copy=False, default=False
    )
    auto_invoice_id = fields.Many2one(
        "account.move",
        string="Source Invoice",
        readonly=True,
        copy=False,
        prefetch=False,
    )

    def _find_company_from_invoice_partner(self):
        self.ensure_one()
        company = (
            self.env["res.company"]
            .sudo()
            .search(
                [
                    ("partner_id", "=", self.commercial_partner_id.id),
                    ("id", "!=", self.company_id.id),
                ],
                limit=1,
            )
        )
        return company or False

    def _set_intercompany_supplier_invoice_ref(self):
        self.ensure_one()
        supplier_invoice = self.auto_invoice_id
        if not supplier_invoice.ref:
            supplier_invoice.write({"ref": self.name})

    def action_post(self):
        """Validated invoice generate cross invoice base on company rules"""
        res = super().action_post()
        # Intercompany account entries or receipts aren't supported
        supported_types = {"out_invoice", "in_invoice", "out_refund", "in_refund"}
        for src_invoice in self.filtered(lambda x: x.move_type in supported_types):
            # do not consider invoices that have already been auto-generated,
            # nor the invoices that were already validated in the past
            dest_company = src_invoice._find_company_from_invoice_partner()
            if not dest_company:
                continue
            # Skip if one of the involved companies have intercompany setting disabled
            if (
                not dest_company.intercompany_invoicing
                or not src_invoice.company_id.intercompany_invoicing
            ):
                continue
            intercompany_user = dest_company.intercompany_invoice_user_id
            if intercompany_user:
                src_invoice = src_invoice.with_user(intercompany_user).sudo()
            else:
                src_invoice = src_invoice.sudo()
            if not src_invoice.auto_generated:
                src_invoice.with_company(dest_company.id).with_context(
                    skip_check_amount_difference=True
                )._inter_company_create_invoice(dest_company)
            if src_invoice.is_sale_document():
                src_invoice._attach_original_pdf_report()
        # set invoice ref on supplier invoice when the customer invoice is validated
        # (case where the source invoice was the supplier one)
        for invoice in self.filtered(
            lambda i: i.is_sale_document() and i.auto_generated
        ):
            invoice.sudo()._set_intercompany_supplier_invoice_ref()
        return res

    def _attach_original_pdf_report(self):
        self.ensure_one()
        supplier_invoice = self.auto_invoice_id
        if not supplier_invoice:
            supplier_invoice = self.search([("auto_invoice_id", "=", self.id)], limit=1)
        report = self.env.ref("account.account_invoices").with_company(self.company_id)
        pdf = report._render_qweb_pdf(report.report_name, [self.id])[0]
        self.env["ir.attachment"].create(
            {
                "name": self._get_report_base_filename() + ".pdf",
                "type": "binary",
                "raw": pdf,
                "res_model": "account.move",
                "res_id": supplier_invoice.id,
                "mimetype": "application/pdf",
            }
        )

    def _check_intercompany_product(self, dest_company):
        self.ensure_one()
        domain = dest_company._get_user_domain()
        dest_user = self.env["res.users"].search(domain, limit=1)
        for line in self.invoice_line_ids:
            try:
                line._check_intercompany_product(dest_user, dest_company)
            except AccessError as e:
                raise UserError(
                    self.env._(
                        "You cannot create invoice in company '%(dest_company_name)s' "
                        "with product '%(product_name)s' because it is not "
                        "multicompany",
                        dest_company_name=dest_company.name,
                        product_name=line.product_id.name,
                    )
                ) from e

    def _check_dest_journal(self, dest_company):
        self.ensure_one()
        dest_journal_type = self._get_destination_journal_type()
        # find the correct journal
        dest_journal = self.env["account.journal"].search(
            [
                *self.env["account.journal"]._check_company_domain(dest_company),
                ("type", "=", dest_journal_type),
            ],
            limit=1,
        )
        if not dest_journal:
            raise UserError(
                self.env._(
                    "Please define %(dest_journal_type)s journal for "
                    'this company: "%(dest_company_name)s" (id:%(dest_company_id)d).',
                    dest_journal_type=dest_journal_type,
                    dest_company_name=dest_company.name,
                    dest_company_id=dest_company.id,
                )
            )
        return dest_journal

    def _inter_company_create_invoice(self, dest_company):
        """create an invoice for the given company : it will copy
            the invoice lines in the new invoice.
        :param dest_company : the company of the created invoice
        :rtype dest_company : res.company record
        """
        self.ensure_one()
        move = self.with_context(check_move_validity=False)
        # check intercompany product
        move._check_intercompany_product(dest_company)
        # if an invoice has already been generated
        # delete it and force the same number
        inter_invoice = move.search(
            [("auto_invoice_id", "=", move.id), ("company_id", "=", dest_company.id)]
        )
        force_number = False
        if inter_invoice and inter_invoice.state in ["draft", "cancel"]:
            force_number = inter_invoice.name
            inter_invoice.with_context(force_delete=True).unlink()
        # create destination invoice
        dest_invoice_data = move._prepare_invoice_data(dest_company)
        if force_number:
            dest_invoice_data["name"] = force_number
        dest_invoice = move.create(dest_invoice_data)
        if dest_invoice.currency_id != move.currency_id:
            dest_invoice.currency_id = move.currency_id
        # create destination invoice lines
        move._create_destination_account_move_line(dest_invoice, dest_company)
        # Validation of destination invoice
        precision = move.env["decimal.precision"].precision_get("Account")
        if dest_company.invoice_auto_validation and not float_compare(
            move.amount_total, dest_invoice.amount_total, precision_digits=precision
        ):
            dest_invoice.action_post()
        else:
            # Add warning in chatter if the total amounts are different
            if float_compare(
                move.amount_total, dest_invoice.amount_total, precision_digits=precision
            ):
                body = move.env._(
                    "WARNING!!!!! Failure in the inter-company invoice "
                    "creation process: the total amount of this invoice "
                    "is %(dest_amount_total)s but the total amount "
                    "of the invoice %(invoice_name)s "
                    "in the company %(company_name)s is %(amount_total)s",
                    dest_amount_total=dest_invoice.amount_total,
                    invoice_name=move.name,
                    company_name=move.company_id.name,
                    amount_total=move.amount_total,
                )
                dest_invoice.message_post(body=body)
        return {"dest_invoice": dest_invoice}

    def _create_destination_account_move_line(self, dest_invoice, dest_company):
        dest_move_line_data = []
        for src_line in self.invoice_line_ids.filtered(
            lambda x: x.display_type == "product"
        ):
            if not src_line.product_id:
                raise UserError(
                    self.env._(
                        "The invoice line '%(line_name)s' doesn't have a product. "
                        "All invoice lines should have a product for "
                        "inter-company invoices.",
                        line_name=src_line.name,
                    )
                )
            dest_move_line_data.append(
                src_line._prepare_account_move_line(dest_invoice, dest_company)
            )
        self.env["account.move.line"].create(dest_move_line_data)

    def _get_destination_invoice_type(self):
        self.ensure_one()
        MAP_INVOICE_TYPE = {
            "out_invoice": "in_invoice",
            "in_invoice": "out_invoice",
            "out_refund": "in_refund",
            "in_refund": "out_refund",
        }
        return MAP_INVOICE_TYPE.get(self.move_type)

    def _get_destination_journal_type(self):
        self.ensure_one()
        MAP_JOURNAL_TYPE = {
            "out_invoice": "purchase",
            "in_invoice": "sale",
            "out_refund": "purchase",
            "in_refund": "sale",
        }
        return MAP_JOURNAL_TYPE.get(self.move_type)

    def _prepare_invoice_data(self, dest_company):
        """Generate invoice values
        :param dest_company : the company of the created invoice
        :rtype dest_company : res.company record
        """
        self.ensure_one()
        move = self.with_context(**clean_context(self.env.context))
        # check if the journal is define in dest company
        dest_journal = move._check_dest_journal(dest_company)
        vals = {
            "move_type": move._get_destination_invoice_type(),
            "partner_id": move.company_id.partner_id.id,
            "company_id": dest_company.id,
            "journal_id": dest_journal.id,
            "ref": move.name,
            "payment_reference": move.payment_reference,
            "invoice_date": move.invoice_date,
            "date": move.date,
            "invoice_origin": move.env._(
                "%(company_name)s - Invoice: %(invoice_name)s",
                company_name=move.company_id.name,
                invoice_name=move.name,
            ),
            "auto_invoice_id": move.id,
            "auto_generated": True,
        }
        # CHECK ME: This field is created by module sale, maybe we need add dependency?
        if (
            hasattr(move, "partner_shipping_id")
            and move.partner_shipping_id
            and not move.partner_shipping_id.company_id
        ):
            # if shipping partner is shared you may want to propagate its value
            # to supplier invoice allowing to analyse invoices
            vals["partner_shipping_id"] = move.partner_shipping_id.id
        return vals

    def button_draft(self):
        for move in self:
            inter_invoice_posted = self.sudo().search(
                [("auto_invoice_id", "=", move.id), ("state", "=", "posted")], limit=1
            )
            if inter_invoice_posted:
                raise UserError(
                    self.env._(
                        "You can't modify this invoice as it has an inter company "
                        "invoice that's in posted state.\n"
                        "Invoice %(invoice_name)s to %(partner_name)s",
                        invoice_name=inter_invoice_posted.name,
                        partner_name=inter_invoice_posted.partner_id.display_name,
                    )
                )
        return super().button_draft()

    def button_cancel(self):
        for invoice in self:
            company = invoice._find_company_from_invoice_partner()
            if company and not invoice.auto_generated:
                for inter_invoice in self.sudo().search(
                    [("auto_invoice_id", "=", invoice.id)]
                ):
                    inter_invoice.button_draft()
                    inter_invoice.write(
                        {
                            "invoice_origin": self.env._(
                                "%(company_name)s - Canceled Invoice: %(invoice_name)s",
                                company_name=invoice.company_id.name,
                                invoice_name=invoice.name,
                            )
                        }
                    )
                    inter_invoice.button_cancel()
        return super().button_cancel()

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get("skip_check_amount_difference"):
            return res
        for move in self.filtered("auto_invoice_id"):
            if (
                float_compare(
                    move.amount_untaxed,
                    move.sudo().auto_invoice_id.amount_untaxed,
                    precision_rounding=move.currency_id.rounding,
                )
                != 0
            ):
                raise UserError(
                    self.env._(
                        "This is an autogenerated multi company invoice and you're "
                        "trying to modify the amount, which will differ from the "
                        "source one (%s)",
                        move.sudo().auto_invoice_id.name,
                    )
                )
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    auto_invoice_line_id = fields.Many2one(
        "account.move.line",
        string="Source Invoice Line",
        readonly=True,
        copy=False,
        prefetch=False,
    )

    def _check_intercompany_product(self, dest_user, dest_company):
        self.product_id.product_tmpl_id.sudo(False).with_user(dest_user).with_context(
            allowed_company_ids=[dest_company.id]
        ).check_access("read")

    @api.model
    def _prepare_account_move_line(self, dest_move, dest_company):
        """Generate invoice line values
        :param dest_move : the created invoice
        :rtype dest_move : account.move record
        :param dest_company : the company of the created invoice
        :rtype dest_company : res.company record
        """
        self.ensure_one()
        vals = {
            "product_id": self.product_id.id or False,
            "price_unit": self.price_unit,
            "product_uom_id": self.product_uom_id.id,
            "quantity": self.quantity,
            "discount": self.discount,
            "move_id": dest_move.id,
            "sequence": self.sequence,
            "auto_invoice_line_id": self.id,
        }
        # Compatibility with module account_invoice_start_end_dates
        if hasattr(self, "start_date") and hasattr(self, "end_date"):
            vals["start_date"] = self.start_date
            vals["end_date"] = self.end_date
        return vals
