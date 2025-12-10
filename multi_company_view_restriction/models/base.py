# Copyright 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class BaseModel(models.AbstractModel):
    _inherit = "base"

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        if view_type in ["form", "tree", "kanban"]:
            restriction = (
                self.env["multicompany.view.restriction"]
                .sudo()
                .search([("name", "=", self._name), ("active", "=", True)], limit=1)
            )
            if restriction and len(self.env.companies) > 1:
                raise UserError(
                    _(
                        "You can not access the view of the model «%s» "
                        "when several companies are active. "
                        "This view is reserved for single-company access."
                    )
                    % self._name
                )
        return super()._get_view(view_id=view_id, view_type=view_type, **options)
