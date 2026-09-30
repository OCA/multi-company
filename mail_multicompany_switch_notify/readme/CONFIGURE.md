No special configuration is needed. Install the module and ensure your
outgoing mail servers have a company assigned via
*Settings → Technical → Outgoing Mail Servers*.

By default, a global/shared mail server (`company_id` = False) does
**not** count as "configured" for a specific company. If a shared
fallback server should be treated as valid for every company, you can
customize the domain in `models/res_company.py`.
