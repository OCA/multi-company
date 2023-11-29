# Copyright 2023 Tecnativa - Pedro M. Baeza
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models


class Base(models.AbstractModel):
    _inherit = "base"

    def _check_company(self, fnames=None):
        """Inject as context the company of the record that is going to be compared
        for being taking into account when computing the company of many2one's
        relations that links with our multi-company models.
        """
        if self._name == "res.company":
            company_source_id = self.id
        elif "company_id" in self._fields:
            company_source_id = self.company_id.id
        self = self.with_context(_check_company_source_id=company_source_id)
        return super()._check_company(fnames=fnames)
