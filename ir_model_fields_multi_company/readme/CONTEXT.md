In multi-company databases, users often need limited access to records
belonging to another company (for example, to update a status or a shared
reference field).

Record rules and ACLs in Odoo usually grant or deny access to the entire
record. There is no standard way to allow writing only a subset of fields
on another company's record.

This module adds a field-level flag so administrators can explicitly allow
editing specific fields in a multi-company scenario while keeping the rest
protected.
