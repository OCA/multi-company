from odoo import api, models


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def render_qweb_html(self, docids, data=None):
        report_model_name = 'report.%s' % self.report_name
        report_model = self.env.get(report_model_name)

        if report_model is not None:
            return super(IrActionsReport, self).render_qweb_html(docids, data)
        else:
            docs = self.env[self.model].browse(docids)
            data = {
                'doc_ids': docids,
                'doc_model': self.model,
                'docs': docs,
                'company_id': self.env['res.company'].browse(
                    [self.env.user.company_id.id]),
            }
        return self.render_template(self.report_name, data), 'html'
