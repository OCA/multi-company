# Copyright 2013-2014 Odoo SA
# Copyright 2015-2017 Chafique Delli <chafique.delli@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)


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

    @api.model
    def _check_intercompany_product(self, dest_user, dest_company):
        try:
            self.product_id.product_tmpl_id.sudo(False).with_user(
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
                    "product_name": self.product_id.name,
                }
            ) from e
