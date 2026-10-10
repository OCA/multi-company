# Copyright 2026-Today: GRAP (https://www.grap.coop)
# Copyright Quentin DUPONT
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.ondelete(at_uninstall=False)
    def _unlink_except_open_session(self):
        if not self.company_id:
            return super()._unlink_except_open_session()
        else:
            product_ctx = dict(self.env.context or {}, active_test=False)
            if self.with_context(**product_ctx).search_count(
                [("id", "in", self.ids), ("available_in_pos", "=", True)]
            ):
                if self.env["pos.session"].search_count([("state", "!=", "closed")]):
                    raise UserError(
                        _(
                            "You cannot delete a product saleable in point of sale "
                            "while a session is still opened."
                        )
                    )


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.ondelete(at_uninstall=False)
    def _unlink_except_active_pos_session(self):
        if not self.company_id:
            return super()._unlink_except_active_pos_session()
        else:
            product_ctx = dict(self.env.context or {}, active_test=False)
            if self.with_context(**product_ctx).search_count(
                [("id", "in", self.ids), ("available_in_pos", "=", True)]
            ):
                if self.env["pos.session"].search_count([("state", "!=", "closed")]):
                    raise UserError(
                        _(
                            "You cannot delete a product saleable in point of sale "
                            "while a session is still opened."
                        )
                    )
