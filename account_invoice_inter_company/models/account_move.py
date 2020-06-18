# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tests.common import Form
from odoo.tools import float_compare


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
            .search([("partner_id", "=", self.partner_id.id)], limit=1)
        )
        return company or False

    def action_post(self):
        """ Validated invoice generate cross invoice base on company rules """
        res = super().action_post()
        for src_invoice in self:
            # do not consider invoices that have already been auto-generated,
            # nor the invoices that were already validated in the past
            dest_company = src_invoice._find_company_from_invoice_partner()
            if not dest_company or src_invoice.auto_generated:
                continue
            intercompany_user = dest_company.intercompany_invoice_user_id
            if intercompany_user:
                src_invoice = src_invoice.with_user(intercompany_user).sudo()
            else:
                src_invoice = src_invoice.sudo()
            src_invoice.with_context(
                force_company=dest_company.id
            )._inter_company_create_invoice(dest_company)
        return res

    def _check_intercompany_product(self, dest_company):
        self.ensure_one()
        if not dest_company.company_share_product:
            return
        domain = dest_company._get_user_domain()
        dest_user = self.env["res.users"].search(domain, limit=1)
        if dest_user:
            for line in self.invoice_line_ids:
                if not line.product_id.with_user(dest_user).check_access_rights("read"):
                    raise UserError(
                        _(
                            "You cannot create invoice in company '%s' with "
                            "product '%s' because it is not multicompany"
                        )
                        % (dest_company.name, line.product_id.name)
                    )

    def _inter_company_create_invoice(self, dest_company):
        """ create an invoice for the given company : it will copy
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
            force_number = inter_invoice.move_name
            inter_invoice.move_name = False
            inter_invoice.unlink()
        # create invoice
        dest_invoice_data = self._prepare_invoice_data(dest_company)
        if force_number:
            dest_invoice_data["move_name"] = force_number
        dest_invoice = self.create(dest_invoice_data)
        # create invoice lines
        dest_move_line_data = []
        for src_line in self.invoice_line_ids:
            if dest_company.company_share_product and not src_line.product_id:
                raise UserError(
                    _(
                        "The invoice line '%s' doesn't have a product. "
                        "All invoice lines should have a product for "
                        "inter-company invoices."
                    )
                    % src_line.name
                )
            dest_move_line_data.append(
                src_line._prepare_account_move_line(dest_invoice, dest_company)
            )
        self.env["account.move.line"].create(dest_move_line_data)
        dest_invoice._move_autocomplete_invoice_lines_values()
        # Validation of account invoice
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
                    "is %s but the total amount of the invoice %s "
                    "in the company %s is %s"
                ) % (
                    dest_invoice.amount_total,
                    self.name,
                    self.company_id.name,
                    self.amount_total,
                )
                dest_invoice.message_post(body=body)
        return {"dest_invoice": dest_invoice}

    def _get_destination_invoice_type(self):
        self.ensure_one()
        MAP_INVOICE_TYPE = {
            "out_invoice": "in_invoice",
            "in_invoice": "out_invoice",
            "out_refund": "in_refund",
            "in_refund": "out_refund",
        }
        return MAP_INVOICE_TYPE.get(self.type)

    def _get_destination_journal_type(self):
        self.ensure_one()
        MAP_JOURNAL_TYPE = {
            "out_invoice": "purchase",
            "in_invoice": "sale",
            "out_refund": "purchase",
            "in_refund": "sale",
        }
        return MAP_JOURNAL_TYPE.get(self.type)

    def _prepare_invoice_data(self, dest_company):
        """ Generate invoice values
            :param dest_company : the company of the created invoice
            :rtype dest_company : res.company record
        """
        self.ensure_one()
        dest_inv_type = self._get_destination_invoice_type()
        dest_journal_type = self._get_destination_journal_type()
        # find the correct journal
        dest_journal = self.env["account.journal"].search(
            [("type", "=", dest_journal_type), ("company_id", "=", dest_company.id)],
            limit=1,
        )
        if not dest_journal:
            raise UserError(
                _('Please define %s journal for this company: "%s" (id:%d).')
                % (dest_journal_type, dest_company.name, dest_company.id)
            )
        # Use test.Form() class to trigger propper onchanges on the invoice
        dest_invoice_data = Form(
            self.env["account.move"].with_context(
                default_type=dest_inv_type, force_company=dest_company.id
            )
        )
        dest_invoice_data.journal_id = dest_journal
        dest_invoice_data.partner_id = self.company_id.partner_id
        dest_invoice_data.ref = self.name
        dest_invoice_data.invoice_date = self.invoice_date
        dest_invoice_data.narration = self.narration
        dest_invoice_data.currency_id = self.currency_id
        vals = dest_invoice_data._values_to_save(all_fields=True)
        vals.update(
            {
                "invoice_origin": _("%s - Invoice: %s")
                % (self.company_id.name, self.name),
                "auto_invoice_id": self.id,
                "auto_generated": True,
            }
        )
        return vals

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
                            "invoice_origin": _("%s - Canceled Invoice: %s")
                            % (invoice.company_id.name, invoice.name)
                        }
                    )
                    inter_invoice.button_cancel()
        return super().button_cancel()


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
        """ Generate invoice line values
            :param dest_move : the created invoice
            :rtype dest_move : account.move record
            :param dest_company : the company of the created invoice
            :rtype dest_company : res.company record
        """
        self.ensure_one()
        # Use test.Form() class to trigger propper onchanges on the line
        product = (
            dest_company.company_share_product
            and self.product_id
            or self.env["product.product"]
        )
        dest_form = Form(
            dest_move.with_context(force_company=dest_company.id),
            "account_invoice_inter_company.view_move_form",
        )
        with dest_form.invoice_line_ids.new() as line_form:
            # HACK: Related fields manually set due to Form() limitations
            line_form.company_id = dest_move.company_id
            # Regular fields
            line_form.display_type = self.display_type
            line_form.product_id = product
            line_form.name = self.name
            if line_form.product_uom_id != self.product_uom_id:
                line_form.product_uom_id = self.product_uom_id
            line_form.quantity = self.quantity
            # TODO: it's wrong to just copy the price_unit
            # You have to check if the tax is price_include True or False
            # in source and target companies
            line_form.price_unit = self.price_unit
            line_form.discount = self.discount
            line_form.sequence = self.sequence
        vals = dest_form._values_to_save(all_fields=True)["invoice_line_ids"][0][2]
        vals.update({"move_id": dest_move.id, "auto_invoice_line_id": self.id})
        if self.analytic_account_id and not self.analytic_account_id.company_id:
            vals["analytic_account_id"] = self.analytic_account_id.id
            analytic_tags = self.analytic_tag_ids.filtered(lambda x: not x.company_id)
            if analytic_tags:
                vals["analytic_tag_ids"] = [(4, x) for x in analytic_tags.ids]
        return vals
