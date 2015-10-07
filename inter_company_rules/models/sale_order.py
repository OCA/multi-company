# -*- coding: utf-8 -*-

from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.exceptions import Warning
from openerp import netsvc, SUPERUSER_ID


class sale_order(orm.Model):

    _inherit = "sale.order"

    _columns = {
        'auto_generated': fields.boolean(
            string='Auto Generated Sale Order'),
        'auto_purchase_order_id': fields.many2one(
            'purchase.order', string='Source Purchase Order', readonly=True)}

    def copy_data(self, cr, uid, _id, default=None, context=None):
        vals = super(sale_order, self).copy_data(cr, uid, _id,
                                                 default, context)
        vals.update({'auto_generated': False,
                     'auto_purchase_order_id': False})
        return vals

    def action_button_confirm(self, cr, uid, ids, context=None):
        """ Generate inter company purchase order based on conditions """
        res = super(sale_order, self).action_button_confirm(cr, uid, ids,
                                                            context=context)
        for order in self.browse(cr, uid, ids, context=context):
            # if company_id not found, return to normal behavior
            if not order.company_id:
                continue
            # if company allow to create a Purchase Order from Sale Order,
            # then do it !
            company = self.pool['res.company']._find_company_from_partner(
                cr, uid, order.partner_id.id, context=context)
            if company and company.po_from_so and (not order.auto_generated):
                self.inter_company_create_purchase_order(
                    cr, uid, order, company, context=context)
        return res

    def inter_company_create_purchase_order(self, cr, uid, order, company,
                                            context=None):
        """ Create a Purchase Order from the current SO (order)
            Note : In this method, reading the current SO is done as sudo,
            and the creation of the derived PO as intercompany_user,
            minimizing the access right required for the trigger user
            :param order : the SO
            :rtype order : sale.order record
            :param company : the company of the created PO
            :rtype company : res.company record
        """
        PurchaseOrder = self.pool['purchase.order']
        company_partner = (order.company_id and order.company_id.partner_id or
                           False)
        if not company or not company_partner.id:
            return

        # find user for creating and validating SO/PO from company
        intercompany_uid = (company.intercompany_user_id and
                            company.intercompany_user_id.id or False)
        if not intercompany_uid:
            raise Warning(_(
                'Provide one user for intercompany relation for % ')
                % company.name)
        # check intercompany user access rights
        if not PurchaseOrder.check_access_rights(
                cr, intercompany_uid, 'create', raise_exception=False):
            raise Warning(_(
                "Inter company user of company %s doesn't have enough "
                "access rights") % company.name)

        # check pricelist currency should be same with SO/PO document
        if order.pricelist_id.currency_id.id != (
            company_partner.property_product_pricelist_purchase.
                currency_id.id):
            raise Warning(_(
                'You cannot create PO from SO because '
                'purchase pricelist currency is different than '
                'sale pricelist currency.'))

        # create the PO and generate its lines from the SO
        PurchaseOrderLine = self.pool['purchase.order.line']
        # read it as sudo,
        # because inter-compagny user can not have the access right on PO
        po_vals = self._prepare_purchase_order_data(
            cr, SUPERUSER_ID, order, company, company_partner, context=context)
        purchase_order_id = PurchaseOrder.create(cr, intercompany_uid,
                                                 po_vals, context=context)
        for line in order.order_line:
            po_line_vals = self._prepare_purchase_order_line_data(
                cr, SUPERUSER_ID, line, order.date_order,
                purchase_order_id, company, context=context)
            PurchaseOrderLine.create(cr, intercompany_uid, po_line_vals,
                                     context=context)

        # write customer reference field on SO
        if not order.client_order_ref:
            purchase_order = PurchaseOrder.browse(
                cr, intercompany_uid, purchase_order_id, context=context)
            order.write({'client_order_ref': purchase_order.name})

        # auto-validate the purchase order if needed
        if company.auto_validation:
            wf_service = netsvc.LocalService('workflow')
            wf_service.trg_validate(intercompany_uid, 'purchase.order',
                                    purchase_order_id, 'purchase_confirm', cr)
        return purchase_order_id

    def _prepare_purchase_order_data(self, cr, uid, order, company,
                                     company_partner, context=None):
        """ Generate purchase order values, from the SO (order)
            :param order : the SO
            :rtype order : sale.order record
            :param company_partner : the partner representing the company of
            the SO
            :rtype company_partner : res.partner record
            :param company : the company in which the PO line will be created
            :rtype company : res.company record
        """
        # find location and warehouse, pick warehouse from company object
        warehouse = (company.warehouse_id and
                     company.warehouse_id.company_id.id == company.id and
                     company.warehouse_id or False)
        if not warehouse:
            raise Warning(_(
                'Configure correct warehouse for company(%s) from '
                'Menu: Settings/companies/companies' % (company.name)))

        return {
            'origin': order.name,
            'partner_id': company_partner.id,
            'location_id': warehouse.lot_input_id.id,
            'pricelist_id': (company_partner.
                             property_product_pricelist_purchase.id),
            'date_order': order.date_order,
            'company_id': company.id,
            'fiscal_position': (company_partner.property_account_position or
                                False),
            'payment_term_id': (company_partner.
                                property_supplier_payment_term.id or False),
            'auto_generated': True,
            'auto_sale_order_id': order.id,
            'partner_ref': order.name,
            'dest_address_id': (order.partner_shipping_id and
                                order.partner_shipping_id.id or False),
        }

    def _prepare_purchase_order_line_data(self, cr, uid,
                                          so_line, date_order, purchase_id,
                                          company, context=None):
        """ Generate purchase order line values, from the SO line
            :param so_line : origin SO line
            :rtype so_line : sale.order.line record
            :param date_order : the date of the orgin SO
            :param purchase_id : the id of the purchase order
            :param company : the company in which the PO line will be created
            :rtype company : res.company record
        """
        # price on PO so_line should be so_line - discount
        price = so_line.price_unit - (so_line.price_unit *
                                      (so_line.discount / 100))

        # computing Default taxes of so_line.
        # It may not affect because of parallel company relation
        taxes = so_line.tax_id
        if so_line.product_id:
            taxes = so_line.product_id.supplier_taxes_id

        # fetch taxes by company not by inter-company user
        company_taxes = [tax_rec.id for tax_rec in taxes
                         if tax_rec.company_id.id == company.id]
        return {
            'name': so_line.name,
            'order_id': purchase_id,
            'product_qty': so_line.product_uom_qty,
            'product_id': (so_line.product_id and so_line.product_id.id or
                           False),
            'product_uom': (so_line.product_id and
                            so_line.product_id.uom_po_id.id or
                            so_line.product_uom.id),
            'price_unit': price or 0.0,
            'company_id': so_line.order_id.company_id.id,
            'date_planned': so_line.order_id.commitment_date or date_order,
            'taxes_id': [(6, 0, company_taxes)],
        }
