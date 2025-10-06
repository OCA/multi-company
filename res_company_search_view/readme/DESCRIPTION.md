This module simply add a search view for the `res.company` model.

It is used to be extended in other modules.

Technically, it is an adaptation of the `res.partner` search view.
(`base.view_res_partner_filter`)

In addition, the following address fields on `res.company` are made stored,
so they become searchable and usable in filters and groupings:

- `street`
- `street2`
- `zip`
- `city`
- `state_id`
- `country_id`
