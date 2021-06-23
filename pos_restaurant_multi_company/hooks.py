# Copyright (C) 2021 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        # Try to guess company id, based on the optional field pos_config_id
        # of the model restaurant.floor
        floors = env["restaurant.floor"].search(
            [('pos_config_id', "!=", False)])
        for floor in floors:
            floor.company_id = floor.pos_config_id.company_id

        # Otherwise, set company_id to False
        floors = env["restaurant.floor"].search(
            [('pos_config_id', "=", False)])
        floors.write({"company_id": False})

        # Initialize printers with no company
        printers = env["restaurant.printer"].search([])
        printers.write({"company_id": False})
