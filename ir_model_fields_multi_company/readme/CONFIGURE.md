To configure this module:

1. Enable Developer Mode.
2. Go to Settings > Technical > Database Structure > Fields.
3. Open the field that should be editable on another company's records.
4. Enable the **Allow Multi-Company Write** field.
5. Save.

Repeat for every field that should be allowed.

If at least one field on the model is marked as allowed, all other fields
on that model are automatically not allowed for editing on another
company's records.
