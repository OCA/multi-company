# -*- coding: utf-8 -*-
# © 2015 Oihane Crucelaegui
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    """Put domain in partner access rule and copy company_id as the default
    value in new field company_ids."""
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        # Change access rule
        rule = env.ref('base.res_partner_rule')
        rule.domain_force = ("['|', "
                             "('company_ids', 'in', user.company_id.id), "
                             "('company_id', '=', False)]")
        # Copy company values
        partner_model = env['res.partner'].with_context(active_test=False)
        groups = partner_model.read_group([], ['company_id'], ['company_id'])
        for group in groups:
            if group['company_id']:
                partners = partner_model.search(group['__domain'])
                partners.write(
                    {'company_ids': [(6, 0, [group['company_id'][0]])]})


def uninstall_hook(cr, registry):
    """Restore partner rule to base value."""
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        rule = env.ref('base.res_partner_rule')
        rule.domain_force = (
            "['|','|',"
            "('company_id.child_ids','child_of',[user.company_id.id]),"
            "('company_id','child_of',[user.company_id.id]),"
            "('company_id','=',False)]")
