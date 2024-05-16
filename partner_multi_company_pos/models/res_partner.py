from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create_from_ui(self, partner):
        if not partner.get("id"):
            partner.update(
                {
                    "company_ids": [(6, 0, [self.env.company.id])]
                    if self.env.company.set_active_company_partner
                    else False
                }
            )
        return super().create_from_ui(partner)
