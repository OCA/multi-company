# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import SUPERUSER_ID, api
from odoo.tools.sql import column_exists, rename_column


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    models = [env["mail.message"]]
    for model in models:
        table_name = model._table
        if column_exists(cr, table_name, "company_id"):
            rename_column(cr, table_name, "company_id", "record_company_id")
