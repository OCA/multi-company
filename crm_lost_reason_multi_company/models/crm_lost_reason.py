# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CrmLostReason(models.Model):
    _inherit = "crm.lost.reason"
    _check_company_auto = True

    company_id = fields.Many2one(
        "res.company",
        "Company",
        ondelete="cascade",
        help="Company that uses this lost reason. "
        "Other companies will not be able to see or use it.",
        index=True,
        default=lambda self: self.env.company,
    )
