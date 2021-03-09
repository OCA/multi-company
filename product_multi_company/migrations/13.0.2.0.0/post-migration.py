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
    for product_product in env["product.product"].search([]):
        if (
            len(product_product.company_ids) == 0
            and len(product_product.product_tmpl_id.company_ids.ids) >= 1
        ):
            product_product.write(
                {
                    "company_ids": [
                        (6, 0, product_product.product_tmpl_id.company_ids.ids)
                    ]
                }
            )
