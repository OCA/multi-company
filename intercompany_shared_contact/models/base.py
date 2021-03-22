# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class Base(models.AbstractModel):
    _inherit = "base"

    def _check_company(self, fnames=None):
        if fnames is None:
            fnames = self._fields
        todo = []
        # Shared partner can be used by every company
        for name in fnames:
            field = self._fields[name]
            if not (
                field.comodel_name == "res.partner"
                and all(self.sudo().mapped(f"{name}.intercompany_readonly_shared"))
            ):
                todo.append(name)
        return super()._check_company(todo)
