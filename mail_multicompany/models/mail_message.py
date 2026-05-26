# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class MailMessage(models.Model):
    _inherit = "mail.message"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("model") and vals.get("res_id"):
                current_object = self.env[vals["model"]].browse(vals["res_id"])
                if hasattr(current_object, "company_id") and current_object.company_id:
                    vals["record_company_id"] = current_object.company_id.id
            if not vals.get("record_company_id"):
                vals["record_company_id"] = self.env.company.id
            if not vals.get("mail_server_id"):
                vals["mail_server_id"] = (
                    self.sudo()
                    .env["ir.mail_server"]
                    .search(
                        [("company_id", "=", vals.get("record_company_id", False))],
                        order="sequence",
                        limit=1,
                    )
                    .id
                )
        return super().create(vals_list)
