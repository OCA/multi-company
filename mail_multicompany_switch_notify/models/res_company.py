# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class ResCompany(models.Model):
    _inherit = "res.company"

    def has_outgoing_mail_server(self):
        """Return True if this company has at least one outgoing mail
        server explicitly assigned to it, via the ``company_id`` field
        that the OCA ``mail_multicompany`` module adds on
        ``ir.mail_server``.

        Called from the frontend (see
        static/src/js/mail_server_company_check.js) right after a user
        switches the active company, to decide whether to show a
        warning notification.

        NOTE: a server with company_id = False is a global/shared
        server and is deliberately NOT counted as "configured" here,
        since the whole point of mail_multicompany is per-company
        routing. If your business rule is that a global fallback server
        should count as configured for every company, change the domain
        below to:
            ['|', ('company_id', '=', self.id), ('company_id', '=', False)]
        """
        self.ensure_one()
        return bool(
            self.env["ir.mail_server"]
            .sudo()
            .search_count([("company_id", "=", self.id)])
        )
