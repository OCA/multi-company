# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    @api.model
    def _name_search(self, name, args=None, operator='ilike',
                     limit=100, name_get_uid=None):
        if self.env.context.get('sudo', False):
            self._cr.execute("""
            SELECT
                j.id AS id,
                CONCAT(j.name, ' (', c.name, ')') AS name
            FROM
                account_journal AS j
            INNER JOIN
                res_company AS c ON c.id = j.company_id
            WHERE
                j.type IN ('bank', 'cash') AND
                j.active = TRUE AND
                j.company_id <> %s AND
                j.id NOT IN (
                    SELECT
                        due_fromto_payment_journal_id
                    FROM
                        res_company
                    WHERE
                        due_fromto_payment_journal_id IS NOT NULL
                )
            ;""" % self.env.user.company_id.id)
            return self._cr.fetchall()
        else:
            return super()._name_search(name, args,
                                        operator, limit,
                                        name_get_uid)
