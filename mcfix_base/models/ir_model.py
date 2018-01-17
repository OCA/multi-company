import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class Base(models.AbstractModel):
    _inherit = 'base'

    def add_company_suffix(self, names):
        res = []
        multicompany_group = self.env.ref('base.group_multi_company')
        if multicompany_group not in self.env.user.groups_id:
            return names
        for name in names:
            rec = self.browse(name[0])
            name = '%s [%s]' % (name[1], rec.company_id.name) if \
                rec.company_id else name[1]
            res += [(rec.id, name)]
        return res

    @api.multi
    @api.depends('company_id')
    def name_get(self):
        names = super(Base, self).name_get()
        if 'company_id' not in self._fields:
            return names
        res = self.add_company_suffix(names)
        return res
