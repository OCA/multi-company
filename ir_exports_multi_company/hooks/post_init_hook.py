# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def post_init_hook(cr, registry):
    cr.execute("""
        UPDATE ir_exports
        SET company_id=res_users.company_id
        FROM res_users
        WHERE res_users.id=ir_exports.create_uid
    """)
