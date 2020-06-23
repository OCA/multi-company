# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    cr.execute(
        """
        INSERT INTO res_partner_res_company_rel
            (res_partner_id, res_company_id)
        SELECT res_partner_id, res_company_assignment_id
        FROM res_partner_res_company_assignment_rel
    """
    )
