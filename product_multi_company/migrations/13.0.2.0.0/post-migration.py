# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, installed_version):
    _logger.debug(
        "Populate new multicompany field on product.product which we added "
        "because it was not correctly inherited from product.template."
    )
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.cr.execute(
        """
        INSERT INTO product_product_res_company_rel
        (product_product_id, res_company_id)
        SELECT pp.id, rel.res_company_id
        FROM product_template_res_company_rel rel
        JOIN product_product pp ON pp.product_tmpl_id = rel.product_template_id
        """
    )
