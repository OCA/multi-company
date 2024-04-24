# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class MailMessage(models.Model):

    _inherit = "mail.message"

    company_id = fields.Many2one("res.company", "Company")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("model") and vals.get("res_id"):
                current_object = self.env[vals["model"]].browse(vals["res_id"])
                if hasattr(current_object, "company_id") and current_object.company_id:
                    vals["company_id"] = current_object.company_id.id
            if not vals.get("company_id"):
                vals["company_id"] = self.env.company.id
            if not vals.get("mail_server_id"):
                mail_server, email_from = self._find_company_mail_server(
                    vals.get("email_from", False), vals.get("company_id", False)
                )
                vals.update(
                    {
                        "mail_server_id": mail_server.id if mail_server else False,
                        "email_from": email_from,
                    }
                )

        return super(MailMessage, self).create(vals_list)

    def _find_company_mail_server(self, email_from, company_id):
        # We want to find the most appropriate mail server for the given email_from
        # but limiting it to the current active company mail servers.
        mail_servers = (
            self.sudo().env["ir.mail_server"].search([("company_id", "=", company_id)])
        )
        if not mail_servers:
            return None, email_from

        return self.env["ir.mail_server"]._find_mail_server(email_from, mail_servers)
