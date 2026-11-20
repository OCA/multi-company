# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2025 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    stage_id = fields.Many2one(check_company=True)

    @api.depends("company_id")
    def _compute_stage_id(self):
        for lead in self:
            if lead.stage_id.company_id and lead.stage_id.company_id != lead.company_id:
                lead.stage_id = False
        return super()._compute_stage_id()

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        # Only return the stages the user has access to due to the new
        # multi company rule
        res = super()._read_group_stage_ids(stages, domain)
        return stages.search([("id", "in", res.ids)])

    def _stage_find(self, team_id=False, domain=None, order="sequence, id", limit=1):
        company_domain = [("company_id", "in", self.company_id.ids + [False])]
        return super()._stage_find(
            team_id=team_id,
            domain=list(domain or []) + company_domain,
            order=order,
            limit=limit,
        )

    def action_set_won(self):
        for leads in self.grouped("company_id").values():
            super(CrmLead, leads).action_set_won()
        return True
