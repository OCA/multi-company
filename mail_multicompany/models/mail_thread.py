# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.model
    def message_process(
        self,
        model,
        message,
        custom_values=None,
        save_original=False,
        strip_attachments=False,
        thread_id=None,
    ):
        context_company = self.env.company
        server_id = self.env.context.get("default_fetchmail_server_id")
        server = self.env["fetchmail.server"].browse(server_id)
        server_company = server.company_id
        if server_company and server_company != context_company:
            context_company = server_company
        return super(MailThread, self.with_company(context_company)).message_process(
            model, message, custom_values, save_original, strip_attachments, thread_id
        )
