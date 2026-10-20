# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, models
from odoo.exceptions import AccessError


class ResCompany(models.Model):
    _inherit = "res.company"

    def has_outgoing_mail_server(self):
        """Return True if an outgoing mail server is assigned to this company.

        Global servers (``company_id`` = False) are not counted, because
        ``mail_multicompany`` only routes messages to a server whose
        ``company_id`` matches the record's company exactly. Without such a
        server, Odoo falls back to the first server by sequence, which may
        belong to another company.
        """
        self.ensure_one()
        if self not in self.env.user.company_ids:
            raise AccessError(
                _("You are not allowed to check the mail servers of this company.")
            )
        return bool(
            self.env["ir.mail_server"]
            .sudo()
            .search_count([("company_id", "=", self.id)], limit=1)
        )
