# -*- coding: utf-8 -*-
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def pre_init_hook(cr):
    cr.execute("update ir_model_data set noupdate=false where "
               "module = 'base' and model = 'res.partner'")
    cr.execute("update ir_model_data set noupdate=false where "
               "module = 'sales_team' and model = 'crm.team'")


def post_init_hook(cr, registry):
    cr.execute("update ir_model_data set noupdate=true where "
               "module = 'base' and model = 'res.partner'")
    cr.execute("update ir_model_data set noupdate=true where "
               "module = 'sales_team' and model = 'crm.team'")
