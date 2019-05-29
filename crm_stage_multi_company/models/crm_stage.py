# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class CrmStage(models.Model):

    _inherit = "crm.stage"

    def _get_default_company_id(self):
        return self.env.user.company_id.id

    def _get_company_id_domain(self):
        return [("id", "child_of", self.env.user.company_id.id)]

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        index=True,
        help="Specific company that uses this stage. "
        "Other companies will not be able to see or use this stage.",
        domain=lambda self: self._get_company_id_domain(),
        default=lambda self: self._get_default_company_id(),
    )