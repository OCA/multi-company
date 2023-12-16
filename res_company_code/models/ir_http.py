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

        # 1. Replace company name by company complete name in the session
        #    The values are used in the switch_company_menu widget (web module)
        # 2. Recompute sequence. (as the widget hard-codes the order by sequence). See :
        #    https://github.com/odoo/odoo/blob/fbd6a3bc10a3302e7061eb46eb246221e461e76d/addons/web/static/src/webclient/switch_company_menu/switch_company_menu.xml#L10  # noqa: B950
        if display_switch_company_menu:
            for sequence, company in enumerate(user.company_ids):
                result["user_companies"]["allowed_companies"].get(company.id).update(
                    {
                        "name": company.complete_name,
                        "sequence": sequence,
                    }
                )
        return result
