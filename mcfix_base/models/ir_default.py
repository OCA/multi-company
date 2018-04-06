# Copyright 2018 Creu Blanca
# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import json
from odoo import api, models, tools


class IrDefault(models.Model):
    _inherit = 'ir.default'

    @api.model
    @tools.ormcache('self.env.uid', 'model_name', 'condition')
    def get_model_defaults(self, model_name, condition=False):
        """Related to  https://github.com/odoo/odoo/pull/23695 """
        super(IrDefault, self).get_model_defaults(
            model_name=model_name, condition=condition)
        cr = self.env.cr
        query = """ SELECT f.name, d.json_value FROM ir_default d
                    JOIN ir_model_fields f ON d.field_id=f.id
                    JOIN res_users u ON u.id=%s
                    WHERE f.model=%s
                        AND (d.user_id IS NULL OR d.user_id=u.id)
                        AND (d.company_id IS NULL OR d.company_id={id1})
                        AND {id2}
                    ORDER BY d.user_id, d.company_id, d.id
                """
        company = self._context.get('default_company_id') or "u.company_id"
        params = [self.env.uid, model_name]
        if condition:
            query = query.format(id1=company, id2="d.condition=%s")
            params.append(condition)
        else:
            query = query.format(id1=company, id2="d.condition IS NULL")
        cr.execute(query, params)
        result = {}
        for row in cr.fetchall():
            # keep the highest priority default for each field
            if row[0] not in result:
                result[row[0]] = json.loads(row[1])
        return result
