No special configuration is needed. Install the module and assign a
company to your outgoing mail servers in
*Settings → Technical → Outgoing Mail Servers*.

A global mail server (no company set) does **not** count as configured
for a company. This matches how `mail_multicompany` routes messages: it
only picks a server whose company is the same as the record's company.
When there is none, Odoo uses the first mail server by sequence, which
may belong to another company.
