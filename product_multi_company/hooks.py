# -*- coding: utf-8 -*-
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    """Put domain in product access rule and copy company_id as the default
    value in new field company_ids."""
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        # Change access rule
        rule = env.ref('product.product_comp_rule')
        rule.domain_force = ("['|', "
                             "('company_ids', 'in', user.company_id.id), "
                             "('company_id', '=', False)]")
        # Copy company values
        template_model = env['product.template']
        groups = template_model.read_group([], ['company_id'], ['company_id'])
        for group in groups:
            if not group['company_id']:
                continue
            templates = template_model.search(group['__domain'])
            templates.write(
                {'company_ids': [(6, 0, [group['company_id'][0]])]})


def uninstall_hook(cr, registry):
    """Restore product rule to base value."""
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        rule = env.ref('product.product_comp_rule')
        rule.domain_force = (" ['|',('company_id','=',user.company_id.id),"
                             "('company_id','=',False)]")
