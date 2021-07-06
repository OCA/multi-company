# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade

from odoo.addons.base_multi_company.hooks import add_no_company_ids


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    spec = [("product.template", "product_multi_company")]
    add_no_company_ids(env, spec)
