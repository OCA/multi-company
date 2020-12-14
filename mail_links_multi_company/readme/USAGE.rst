The module works correctly on emails where at least one link to an odoo
record exists, i.e. <a href="/foo?model=bar.zaz&res_id=1" ...>Link to record</>.
It will go over all links in the email html body and try to find one that has
a company with the web_base_url_mail field set. If it doesn't, it simply falls
back to the default behaviour of using the web.base.url configuration parameter.
