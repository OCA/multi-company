def pre_init_partner_phone(env):
    """
    Controleer or the column 'phone' exists in the tabel 'res_partner'
    1. Rename column phone in res_partner to phone_old
    2. Add a new JSONB column called phone to res_partner table
    3. Populate the new phone column with JSON values containing all
       companies from res_company as keys and phone_old as values
    4. Remove the phone_old column from res_partner
    Clean up temporary table
    :param env:
    :return:
    """
    query = """
        DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'res_partner'
                    AND data_type = 'character varying'
                    AND column_name = 'phone'
                ) THEN
                    ALTER TABLE res_partner
                    RENAME COLUMN phone TO phone_old;

                    ALTER TABLE res_partner
                    ADD COLUMN phone JSONB;

                    UPDATE res_partner rp
                    SET phone = (
                        SELECT jsonb_object_agg(rc.id, rp.phone_old)
                        FROM res_company rc
                    );

                    ALTER TABLE res_partner
                    DROP COLUMN phone_old;
                END IF;
            END $$;
        """
    env.cr.execute(query)
