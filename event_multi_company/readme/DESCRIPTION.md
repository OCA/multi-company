Based on ``base_multi_company`` module.
Adds a ``company_ids`` Many2many on ``event.event`` so an event can be assigned
to several companies at once. The standard ``company_id`` field becomes a
computed/searched proxy over ``company_ids`` via ``multi.company.abstract``.

Backend visibility is handled transparently by Odoo's standard multi-company
record rule on ``event.event``, which ``multi.company.abstract`` automatically
reroutes through ``company_ids``.

If the optional ``website_event`` module is installed, the same rule applies
to the public ``/event`` listing on each website: an event is only displayed
on the websites of the companies listed in its ``company_ids``. No bridge
module is needed.

Same pattern as ``product_multi_company`` and ``partner_multi_company``.
