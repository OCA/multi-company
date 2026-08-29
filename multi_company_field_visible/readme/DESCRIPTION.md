The OCA multi-company stack (`base_multi_company` and its satellites)
adds a `Companies` field that scopes a record to one or more companies,
but hides it behind the `base.group_multi_company` group. Users without
that group -- a single-company merchant, for example -- cannot see or
set the company of their own records.

This module adds an `Own Company` proxy field on every model based on
`multi.company.abstract`. It lets those users see and manage **only
their own company**:

- The real `company_ids` value is never exposed, so a record shared with
  (or global to) other companies never reveals them.
- Edits are merged: changing the own company never wipes the access
  granted to companies the user cannot see.
- The field can never be left blank for these users; it falls back to
  their current company.

This is the base module: it carries the logic but exposes nothing on its
own. Install one of the bridge modules
(`partner_multi_company_field_visible`,
`product_multi_company_field_visible`) to expose the field on a given
model.
