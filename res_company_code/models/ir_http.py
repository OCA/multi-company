# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.http import request


class Http(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):

        result = super().session_info()
        user = request.env.user
        display_switch_company_menu = (
            user.has_group("base.group_multi_company") and len(user.company_ids) > 1
        )

        # Replace company name by company complete name in the session
        # The values are used in the switch_company_menu widget (web module)
        result["user_companies"]["current_company"] = (
            user.company_id.id,
            user.company_id.complete_name,
        )
        if display_switch_company_menu:
            result["user_companies"]["allowed_companies"] = [
                (comp.id, comp.complete_name) for comp in user.company_ids
            ]
        return result
