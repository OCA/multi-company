# -*- coding: utf-8 -*-
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp import SUPERUSER_ID


class res_company(orm.Model):

    _inherit = 'res.company'

    _columns = {
        'so_from_po': fields.boolean(
            string="Create Sale Orders when buying to this company",
            help="Generate a Sale Order when a Purchase Order with this "
            "company as supplier is created.\n The intercompany user must at "
            "least be Sale User."),
        'po_from_so': fields.boolean(
            string="Create Purchase Orders when selling to this company",
            help="Generate a Purchase Order when a Sale Order with this "
            "company as customer is created.\n The intercompany user must at "
            "least be Purchase User."),
        'auto_generate_invoices': fields.boolean(
            string="Create Invoices/Refunds when encoding invoices/refunds "
            "made to this company",
            help="Generate Customer/Supplier Invoices (and refunds) "
            "when encoding invoices (or refunds) made to this company.\n "
            "e.g: Generate a Customer Invoice when a Supplier Invoice with "
            "this company as supplier is created."),
        'auto_validation': fields.boolean(
            string="Sale/Purchase Orders Auto Validation",
            help="When a Sale Order or a Purchase Order is created by "
            "a multi company rule for this company, "
            "it will automatically validate it"),
        'intercompany_user_id': fields.many2one(
            "res.users", string="Inter Company User",
            help="Responsible user for creation of documents triggered by "
            "intercompany rules."),
        'warehouse_id': fields.many2one(
            "stock.warehouse", string="Warehouse For Purchase Orders",
            help="Default value to set on Purchase Orders that "
            "will be created based on Sale Orders made to this company")
    }

    _defaults = {
        'intercompany_user_id': lambda self, cr, uid,
        context=None: SUPERUSER_ID,
    }

    def _find_company_from_partner(self, cr, uid, partner_id, context=None):
        company_id = self.search(cr, SUPERUSER_ID,
                                 [('partner_id', '=', partner_id)],
                                 limit=1, context=context)
        if not company_id:
            return False
        return self.browse(cr, SUPERUSER_ID, company_id[0], context=context)

    def _check_intercompany_missmatch_selection(self, cr, uid, ids,
                                                context=None):
        for company in self.browse(cr, uid, ids, context=context):
            if ((company.po_from_so or company.so_from_po) and
                    company.auto_generate_invoices):
                return False
        return True

    _constraints = [
        (_check_intercompany_missmatch_selection,
         _("You cannot select to create invoices based on other "
           "invoices simultaneously with another option '"
           "('Create Sale Orders when buying to this company' or"
           "'Create Purchase Orders when selling to this company')!"),
         ['po_from_so', 'so_from_po', 'auto_generate_invoices'],),
    ]
