# Copyright 2024 ForgeFlow S.L. (http://www.forgeflow.com)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=W8150
from odoo.addons.partner_multi_company import hooks


def migrate(cr, version):
    hooks.fix_user_partner_companies(cr)
