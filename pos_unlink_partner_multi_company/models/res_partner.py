# Copyright 2026-Today: GRAP (https://www.grap.coop)
# Copyright Quentin DUPONT
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.ondelete(at_uninstall=False)
    def _unlink_except_active_pos_session(self):
        if not self.company_id:
            return super()._unlink_except_active_pos_session()
        else:
            running_sessions = self.env["pos.session"].search(
                [("state", "!=", "closed")]
            )
            if running_sessions:
                raise UserError(
                    _(
                        "You cannot delete contacts while there are active "
                        "PoS sessions. Close the session(s) %s first."
                    )
                    % ", ".join(session.name for session in running_sessions)
                )
