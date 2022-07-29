from . import models


def post_init_hook(cr, registry):
    cr.execute("UPDATE product_category SET company_id=null")
