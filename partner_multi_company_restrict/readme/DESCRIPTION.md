This module restricts visibility of contacts linked to internal users
(colleagues) to the companies a user actually belongs to, on top of
`partner_multi_company`'s company scoping.

Odoo's standard `res.partner` record rule always shows contacts linked to
an internal user (`partner_share = False`), regardless of company, so that
"assigned to" pickers and similar widgets keep working. This means any
user can see (and interact with) the contact record of any colleague,
even one from a company they have no relationship with at all.

This module adds a second, global record rule: a user only sees a
colleague's contact if at least one of these holds:

- it belongs to one of their own companies (this is the whole point:
  a user allowed into 2 out of 50 companies stays scoped to those 2,
  *regardless* of whether they have multi-company access -- there is no
  group-based bypass);
- it is their own contact (safety net);
- it has been deliberately shared (blank *Companies*, the same convention
  used across the `multi_company_field_visible` stack);
- it is not actually an internal user's contact in the first place (e.g. a
  portal customer), which is unaffected by this rule and keeps following
  the normal company scoping.

A real system administrator does not need a bypass here: pair this with
`res_company_admin_sync`, which keeps administrators assigned to every
company automatically, so the plain company-scoping condition above
already lets them see everything.

The restriction can be turned off from *Settings > General Settings >
Companies* if it breaks a legitimate use case, such as adding a colleague
as a follower on a shared document.

To also hide contacts linked to system administrators from regular users
(a separate, non-multi-company concern), install
`partner_hide_admin_contact` alongside this module.

## Company records

A company's own contact (e.g. the partner behind "My Company") is created
with a blank `company_ids`, the "shared with everyone" convention used
across this stack -- which meant it stayed visible to every user
regardless of company. This module's `post_init_hook` scopes every
pre-existing company's contact to itself, and a `res.company` override
does the same for any company created afterwards, so the company-scoping
rules above apply to it too: a user only sees another company's own
contact card if they are actually assigned to that company (or it was
deliberately re-shared by clearing its `Companies` field again).

