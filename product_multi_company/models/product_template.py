# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class ProductTemplate(models.Model):
    _inherit = ["multi.company.abstract", "product.template"]
    _name = "product.template"

    def web_save(self, vals, specification, next_id=None):
        # The form sends the company_id recomputed by the onchange together with
        # company_ids. Drop it before the write chain: write overrides of modules
        # loaded after this one (stock, sale_timesheet) check company_id before
        # MultiCompanyAbstract.write discards it, and read it as a company change.
        self._multicompany_patch_vals(vals)
        return super().web_save(vals, specification, next_id=next_id)
