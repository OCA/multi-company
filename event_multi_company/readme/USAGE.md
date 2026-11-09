On the event form, the standard *Company* field is replaced by a *Companies*
many2many tags field (visible to users of the *Multi Companies* group).

* Leave it empty → event accessible from every company (legacy behaviour).
* Pick one or several companies → event accessible only to users of those
  companies.

If the ``website_event`` module is installed:

* An event with empty ``company_ids`` is displayed on every website.
* An event with one or more companies is only displayed on the websites of
  those companies.
* If you also set the per-event *Website* field, the event is restricted to
  that single website. The website's company must be one of the event's
  companies (upstream constraint).
