# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2025 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    stage_id = fields.Many2one(check_company=True)

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        # Only return the stages the user has access to due to the new
        # multi company rule
        res = super()._read_group_stage_ids(stages, domain)
        return stages.search([("id", "in", res.ids)])
