Warns the user when they switch the active company (top-right company
selector) to a company that has no dedicated outgoing mail server
configured.

This module depends on `mail_multicompany` which adds a `company_id`
field on `ir.mail_server`. When the user switches companies, a check is
performed and a sticky warning notification is shown if no server is
assigned to the newly active company.
