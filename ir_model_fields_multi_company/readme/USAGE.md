To use this module:

1. Switch to My Company (San Francisco).
2. Open a record belonging to My Company (Chicago) (visible through
   multi-company access / record rules).
3. Change only fields allowed for multi-company write and save — the record
   is saved successfully.
4. Change any field that is not allowed for editing and save — a `UserError`
   appears listing the fields that are not allowed for editing.

If the record belongs to one of the companies available to the user
(`env.companies`), fields are edited as usual (subject to standard ACL /
record rules).
