# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    partner_multi_company_restrict_cross_company = fields.Boolean(
        string="Restrict internal-user contacts to own company",
        help="Regular internal users (without multi-company access) keep "
        "seeing their own company's colleagues, but no longer see "
        "colleagues from another company. Disable if this breaks a "
        "legitimate use case, such as adding a colleague as a follower.",
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        rule = self.env.ref(
            "partner_multi_company_restrict.res_partner_rule_restrict_cross_company",
            raise_if_not_found=False,
        )
        res["partner_multi_company_restrict_cross_company"] = bool(rule and rule.active)
        return res

    def set_values(self):
        result = super().set_values()
        rule = self.env.ref(
            "partner_multi_company_restrict.res_partner_rule_restrict_cross_company",
            raise_if_not_found=False,
        )
        if rule:
            rule.sudo().active = self.partner_multi_company_restrict_cross_company
        return result
