This module extends `ir.model.fields` with a boolean flag that marks a field
as allowed for editing on another company's records.

If a user edits a record whose `company_id` is not among the companies
available to them (`env.companies`), only fields with the flag enabled may
be changed. As soon as at least one field on the model is marked as allowed,
access to all other fields on that model is automatically denied.

If the `write` values contain at least one field that is not allowed for
editing, a `UserError` is raised listing those fields.

Technical fields (`id`, `create_uid`, `create_date`, `write_uid`,
`write_date`, and similar ones) are not taken into account during the check.

The module restrictions do not apply to records belonging to companies
available to the user. Restrictions also do not apply when the write is
performed as a superuser (`self.env.su`): in that case, all fields can be
edited.
