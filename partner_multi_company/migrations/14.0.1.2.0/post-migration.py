def migrate(cr, version):
    # Backfill the user-partner sync that earlier versions of post_init_hook
    # missed. Existing installations have user-partner records anchored to a
    # single company (the legacy partner.company_id), even though the user
    # may be allowed in several companies. Logging in under any company
    # other than that one fails with AccessError.
    #
    # See https://github.com/OCA/multi-company/issues/995 (and #438).
    cr.execute(
        """
        INSERT INTO res_company_res_partner_rel (res_partner_id, res_company_id)
        SELECT u.partner_id, rel.cid
        FROM res_users u
        JOIN res_company_users_rel rel ON rel.user_id = u.id
        WHERE u.partner_id IS NOT NULL
        ON CONFLICT DO NOTHING
        """
    )
