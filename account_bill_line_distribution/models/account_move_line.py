# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    distribution_ids = fields.One2many(
        "account.invoice.line.distribution",
        "invoice_line_id",
        string="Distribution",
        copy=True,
    )

    @api.onchange("quantity", "price_unit")
    def _onchange_comp_amount_percent(self):
        for dist_line in self.distribution_ids:
            dist_line.update({"amount": 0.0, "percent": 100})
            dist_line._onchange_amount_total()
            dist_line._onchange_percent_total()

    def get_default_distribution(self):
        return {
            "percent": 100.00,
            "company_id": self.env.context.get("company_id")
            or self.company_id.id
            or self.move_id.company_id.id
            or self.env.user.company_id.id,
        }

    @api.model_create_multi
    def create(self, vals_list):
        lines = super(AccountMoveLine, self).create(vals_list)
        invoice_line = lines.filtered(
            lambda line: line.move_id.move_type
            in (
                "out_invoice",
                "in_invoice",
                "out_refund",
                "in_refund",
                "out_receipt",
                "in_receipt",
            )
        )
        for line in invoice_line.filtered(lambda l: not l.distribution_ids):
            line.write({"distribution_ids": [(0, 0, line.get_default_distribution())]})
            line.distribution_ids._onchange_percent_total()
        return lines

    def write(self, vals):
        super(AccountMoveLine, self).write(vals)
        if "price_unit" in vals or "quantity" in vals:
            self.distribution_ids._onchange_percent_total()

    @api.constrains("distribution_ids")
    def _check_percentage(self):
        for line in self.filtered(
            lambda line: line.move_id.move_type
            in (
                "out_invoice",
                "in_invoice",
                "out_refund",
                "in_refund",
                "out_receipt",
                "in_receipt",
            )
            and not line.tax_exigible
        ):
            total = sum(line.distribution_ids.mapped("percent"))
            if total != 100.00:
                raise ValidationError(
                    _("The distribution for {} does not total to 100%.").format(
                        line.name
                    )
                )

    @api.onchange("distribution_ids")
    def _onchange_distribution_ids_percent(self):
        percentage = 0.00
        if self.distribution_ids:
            i = 0
            for dist in self.distribution_ids:
                if dist.company_id != self.env.user.company_id:
                    percentage += dist.percent
                else:
                    index = i
                i += 1
            if "index" in locals():
                self.distribution_ids[index].percent = 100.00 - percentage
        else:
            self.distribution_ids = [(0, 0, self.get_default_distribution())]

    @api.onchange("distribution_ids")
    def _onchange_distribution_ids_amount(self):
        amount = 0.00
        if self.distribution_ids:
            i = 0
            for dist in self.distribution_ids:
                if dist.company_id != self.env.user.company_id:
                    amount += dist.amount
                else:
                    index = i
                i += 1
            if "index" in locals():
                self.distribution_ids[index].amount = self.price_subtotal - amount
        else:
            self.distribution_ids = [(0, 0, self.get_default_distribution())]

    def open_line_view(self):
        self.ensure_one()
        view = self.env.ref(
            "account_bill_line_distribution.move_line_distribution_form"
        )
        return {
            "name": _("Distribution lines"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "account.move.line",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": self.id,
            "context": dict(
                self.env.context,
            ),
        }
