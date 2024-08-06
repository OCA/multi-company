# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
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

    def action_post(self):
        """Validated invoice generate cross invoice base on company rules"""
        res = super().action_post()
        # Intercompany account entries or receipts aren't supported
        supported_types = {"out_invoice", "in_invoice", "out_refund", "in_refund"}
        for src_invoice in self.filtered(lambda x: x.move_type in supported_types):
            # do not consider invoices that have already been auto-generated,
            # nor the invoices that were already validated in the past
            dest_company = src_invoice._find_company_from_invoice_partner()
            if not dest_company or src_invoice.auto_generated:
                continue
            # If one of the involved companies have the intercompany setting disabled, skip
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
            src_invoice.with_company(dest_company.id).with_context(
                skip_check_amount_difference=True
            )._inter_company_create_invoice(dest_company)
        return res

    def _check_intercompany_product(self, dest_company):
        self.ensure_one()
        if dest_company.company_share_product:
            return
        domain = dest_company._get_user_domain()
        dest_user = self.env["res.users"].search(domain, limit=1)
        for line in self.invoice_line_ids:
            try:
                line.product_id.product_tmpl_id.sudo(False).with_user(
                    dest_user
                ).with_context(
                    **{"allowed_company_ids": [dest_company.id]}
                ).check_access_rule(
                    "read"
                )
            except AccessError as e:
                raise UserError(
                    _(
                        "You cannot create invoice in company '%(dest_company_name)s' with "
                        "product '%(product_name)s' because it is not multicompany"
                    )
                    % {
                        "dest_company_name": dest_company.name,
                        "product_name": line.product_id.name,
                    }
                ) from e

    def _check_dest_journal(self, dest_company):
        self.ensure_one()
        dest_journal_type = self._get_destination_journal_type()
        # find the correct journal
        dest_journal = self.env["account.journal"].search(
            [("type", "=", dest_journal_type), ("company_id", "=", dest_company.id)],
            limit=1,
        )
        if not dest_journal:
            raise UserError(
                _(
                    "Please define %(dest_journal_type)s journal for "
                    'this company: "%(dest_company_name)s" (id:%(dest_company_id)d).'
                )
                % {
                    "dest_journal_type": dest_journal_type,
                    "dest_company_name": dest_company.name,
                    "dest_company_id": dest_company.id,
                }
            )

    def _inter_company_create_invoice(self, dest_company):
        """create an invoice for the given company : it will copy
            the invoice lines in the new invoice.
        :param dest_company : the company of the created invoice
        :rtype dest_company : res.company record
        """
        self.ensure_one()
        self = self.with_context(check_move_validity=False)
        # check intercompany product
        self._check_intercompany_product(dest_company)
        # if an invoice has already been generated
        # delete it and force the same number
        inter_invoice = self.search(
            [("auto_invoice_id", "=", self.id), ("company_id", "=", dest_company.id)]
        )
        force_number = False
        if inter_invoice and inter_invoice.state in ["draft", "cancel"]:
            force_number = inter_invoice.name
            inter_invoice.with_context(force_delete=True).unlink()
        # create destination invoice
        dest_invoice_data = self._prepare_invoice_data(dest_company)
        if force_number:
            dest_invoice_data["name"] = force_number
        dest_invoice = self.create(dest_invoice_data)
        if dest_invoice.currency_id != self.currency_id:
            dest_invoice.currency_id = self.currency_id
        # create destination invoice lines
        self._create_destination_account_move_line(dest_invoice, dest_company)
        # Validation of destination invoice
        precision = self.env["decimal.precision"].precision_get("Account")
        if dest_company.invoice_auto_validation and not float_compare(
            self.amount_total, dest_invoice.amount_total, precision_digits=precision
        ):
            dest_invoice.action_post()
        else:
            # Add warning in chatter if the total amounts are different
            if float_compare(
                self.amount_total, dest_invoice.amount_total, precision_digits=precision
            ):
                body = _(
                    "WARNING!!!!! Failure in the inter-company invoice "
                    "creation process: the total amount of this invoice "
                    "is %(dest_amount_total)s but the total amount "
                    "of the invoice %(invoice_name)s "
                    "in the company %(company_name)s is %(amount_total)s"
                ) % {
                    "dest_amount_total": dest_invoice.amount_total,
                    "invoice_name": self.name,
                    "company_name": self.company_id.name,
                    "amount_total": self.amount_total,
                }
                dest_invoice.message_post(body=body)
        return {"dest_invoice": dest_invoice}

    def _create_destination_account_move_line(self, dest_invoice, dest_company):
        dest_move_line_data = []
        for src_line in self.invoice_line_ids.filtered(
            lambda x: x.display_type == "product"
        ):
            if not src_line.product_id:
                raise UserError(
                    _(
                        "The invoice line '%(line_name)s' doesn't have a product. "
                        "All invoice lines should have a product for "
                        "inter-company invoices."
                    )
                    % {"line_name": src_line.name}
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
        self = self.with_context(**clean_context(self.env.context))
        # check if the journal is define in dest company
        self._check_dest_journal(dest_company)
        vals = {
            "move_type": self._get_destination_invoice_type(),
            "partner_id": self.company_id.partner_id.id,
            "ref": self.name,
            "invoice_date": self.invoice_date,
            "invoice_origin": _("%(company_name)s - Invoice: %(invoice_name)s")
            % {"company_name": self.company_id.name, "invoice_name": self.name},
            "auto_invoice_id": self.id,
            "auto_generated": True,
        }
        return vals

    def button_draft(self):
        for move in self:
            inter_invoice_posted = self.sudo().search(
                [("auto_invoice_id", "=", move.id), ("state", "=", "posted")], limit=1
            )
            if inter_invoice_posted:
                raise UserError(
                    _(
                        "You can't modify this invoice as it has an inter company "
                        "invoice that's in posted state.\n"
                        "Invoice %(invoice_name)s to %(partner_name)s"
                    )
                    % {
                        "invoice_name": inter_invoice_posted.name,
                        "partner_name": inter_invoice_posted.partner_id.display_name,
                    }
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
                            "invoice_origin": _(
                                "%(company_name)s - Canceled Invoice: %(invoice_name)s"
                            )
                            % {
                                "company_name": invoice.company_id.name,
                                "invoice_name": invoice.name,
                            }
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
                    _(
                        "This is an autogenerated multi company invoice and you're "
                        "trying to modify the amount, which will differ from the "
                        "source one (%s)"
                    )
                    % (move.sudo().auto_invoice_id.name)
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
