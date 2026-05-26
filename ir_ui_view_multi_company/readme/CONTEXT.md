In complex multi-company environments, it is common for different companies
to require personalized views for the same model. Examples include:

- Different workflows or business processes.
- Variations in required fields or field ordering.
- Regulatory or organizational differences between subsidiaries.

Previously, these needs were often addressed by assigning views to
security groups using the `groups_id` attribute. However, this is no longer
supported.

The `ir_ui_view_multi_company` module resolves this limitation by introducing
a dedicated `company_ids` field on views, ensuring that views are only applied
when the user is operating under the matching company context.
