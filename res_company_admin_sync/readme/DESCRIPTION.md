Keeps system administrators (`base.group_system`) in sync with every
company in the database, automatically.

Found in production during the Canarias Conectada migration: several
administrator accounts were missing dozens of companies from their
allowed companies (`res.users.company_ids`), including the most recently
created ones, because nothing added a new company to the existing
administrators, nor granted a newly-promoted administrator access to the
companies that already existed. Since the company switcher is driven by
`company_ids` (not by the broader access rights an administrator already
holds), this left administrators unable to switch into companies they
should obviously be able to manage.

This module closes both directions of that gap:

- when a company is created, every existing system administrator gets it
  added to their allowed companies;
- when a user is granted the *Administration / Settings* group, every
  existing company gets added to their allowed companies.

No configuration needed; this is meant to always be on.
