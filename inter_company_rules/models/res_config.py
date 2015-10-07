# -*- coding: utf-8 -*-
from openerp.osv import orm, fields


class inter_company_rules_configuration(orm.TransientModel):

    _inherit = 'base.config.settings'

    _columns = {
        'company_id': fields.many2one(
            'res.company', string='Select Company',
            help='Select company to setup Inter company rules.'),
        'rule_type': fields.selection(
            [('so_and_po', 'SO and PO setting for inter company'),
             ('invoice_and_refunds',
              'Create Invoice/Refunds when encoding invoice/refunds')],
            string='Type of inter company rules',
            help='Select the type to setup inter company rules in '
            'selected company.'),
        'so_from_po': fields.boolean(
            string='Create Sale Orders when buying to this company',
            help='Generate a Sale Order when a Purchase Order with this '
            'company as supplier is created.'),
        'po_from_so': fields.boolean(
            string='Create Purchase Orders when selling to this company',
            help='Generate a Purchase Order when a Sale Order with this '
            'company as customer is created.'),
        'auto_validation': fields.boolean(
            string='Sale/Purchase Orders Auto Validation',
            help='When a Sale Order or a Purchase Order is created by a multi '
            'company rule for this company, it will automatically validate it.'
        ),
        'warehouse_id': fields.many2one(
            'stock.warehouse', string='Warehouse For Purchase Orders',
            help='Default value to set on Purchase Orders that will be '
            'created based on Sale Orders made to this company.'),
    }

    def onchange_rule_type(self, cr, uid, ids, rule_type, context=None):
        res = {'value': {}}
        if rule_type == 'invoice_and_refunds':
            res['value']['so_from_po'] = False
            res['value']['po_from_so'] = False
            res['value']['auto_validation'] = False

        elif rule_type == 'so_and_po':
            res['value']['invoice_and_refunds'] = False
        return res

    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        res = {'value': {}}
        if company_id:
            rule_type = False
            company = self.pool['res.company'].browse(cr, uid, company_id,
                                                      context=context)
            if (company.so_from_po or company.po_from_so or
                    company.auto_validation):
                rule_type = 'so_and_po'
            elif company.auto_generate_invoices:
                rule_type = 'invoice_and_refunds'

            res['value']['rule_type'] = rule_type
            res['value']['so_from_po'] = company.so_from_po
            res['value']['po_from_so'] = company.po_from_so
            res['value']['auto_validation'] = company.auto_validation
            res['value']['warehouse_id'] = company.warehouse_id.id
        return res

    def set_inter_company_configuration(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context=context)
        if config.company_id:
            vals = {
                'so_from_po': config.so_from_po,
                'po_from_so': config.po_from_so,
                'auto_validation': config.auto_validation,
                'auto_generate_invoices': (
                    True if config.rule_type == 'invoice_and_refunds'
                    else False),
                'warehouse_id': config.warehouse_id.id
            }
            config.company_id.write(vals)
