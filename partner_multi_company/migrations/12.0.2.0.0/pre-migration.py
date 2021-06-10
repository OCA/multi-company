# Copyright 2021 Tecnativa - David Vidal
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """When this relation comes up in the reconciliation widget it we could run
    into some nasty exeption due to how Odoo prepares the query, subtituting
    and `res_partner` occurrence to the `p3` join alias, which a subquery won't
    be aware of
    odoo/odoo/blob/12.0/addons/account/models/reconciliation_widget.py#L103
    So we rename the table and the column to avoid such errors.
    """
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE res_company_assignment_res_partner_rel
        RENAME COLUMN res_partner_id TO partner_id
        """
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE res_company_assignment_res_partner_rel
        RENAME TO partner_res_company_assignment_rel
        """
    )
