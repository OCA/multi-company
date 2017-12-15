# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade
from odoo.addons.base_multi_company import hooks


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_tables(
        env.cr, [
            ('product_template_res_company_rel',
             'product_template_res_company_assignment_rel'),
        ],
    )
    openupgrade.rename_columns(
        env.cr, {
            'product_template_res_company_assignment_rel': [
                ('res_company_id', 'res_company_assignment_id'),
            ],
        }
    )
    hooks.set_security_rule(env, 'product.product_comp_rule')
