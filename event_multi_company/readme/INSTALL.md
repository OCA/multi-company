Depends on ``base_multi_company`` (OCA/multi-company) and ``event`` (core).

A ``post_init_hook`` copies each event's existing ``company_id`` into the new
``company_ids`` field, so pre-existing events keep their visibility.

Uninstall does **not** automatically restore the upstream ``company_id``
behaviour. Run ``-u event`` afterwards (or restore from a backup) to fully
revert.
