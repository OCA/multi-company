from odoo import api, models
from odoo.osv import expression


class IrMailServer(models.Model):
    _inherit = "ir.mail_server"

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        domain = []
        if not self._context.get('show_all'):
            domain = ['|', ("company_id", "=", self.env.company.id), ('company_id', '=', False)]
        args = expression.AND((args, domain))       
            
        return super().search(
            args, offset=offset, limit=limit, order=order, count=count
        )
