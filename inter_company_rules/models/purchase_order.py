# -*- coding: utf-8 -*-
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.exceptions import Warning
from openerp import netsvc, SUPERUSER_ID


class purchase_order(orm.Model):

    _inherit = "purchase.order"

    _columns = {
        'auto_generated': fields.boolean(
            string='Auto Generated Purchase Order'),
        'auto_sale_order_id': fields.many2one('sale.order',
                                              string='Source Sale Order',
                                              readonly=True)}

    def copy_data(self, cr, uid, _id, default=None, context=None):
        vals = super(purchase_order, self).copy_data(cr, uid, _id,
                                                     default, context)
        vals.update({'auto_generated': False,
                     'auto_sale_order_id': False})
        return vals

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        """ Generate inter company sale order base on conditions."""
        res = super(purchase_order, self).wkf_confirm_order(cr, uid, ids,
                                                            context=context)
        for order in self.browse(cr, uid, ids, context=context):
            # get the company from partner then trigger action of
            # intercompany relation
            company_rec = self.pool['res.company']._find_company_from_partner(
                cr, uid, order.partner_id.id, context=context)
            if company_rec and company_rec.so_from_po and (
                    not order.auto_generated):
                self.inter_company_create_sale_order(cr, uid, order,
                                                     company_rec,
                                                     context=context)
        return res

    def inter_company_create_sale_order(self, cr, uid, order, company,
                                        context=None):
        """ Create a Sale Order from the current PO (order)
            Note : In this method, reading the current PO is done as sudo,
            and the creation of the derived
            SO as intercompany_user, minimizing the access right required
            for the trigger user.
            :param order : the PO
            :rtype order : purchase.order
            :param company : the company of the created PO
            :rtype company : res.company record
        """
        SaleOrder = self.pool['sale.order']
        company_partner = order.company_id.partner_id

        # find user for creating and validation SO/PO from partner company
        intercompany_uid = (company.intercompany_user_id and
                            company.intercompany_user_id.id or False)
        if not intercompany_uid:
            raise Warning(_(
                'Provide at least one user for inter company relation for % ')
                % company.name)
        # check intercompany user access rights
        if not SaleOrder.check_access_rights(
                cr, intercompany_uid, 'create', raise_exception=False):
            raise Warning(_(
                "Inter company user of company %s doesn't have enough "
                "access rights") % company.name)

        # check pricelist currency should be same with SO/PO document
        if order.pricelist_id.currency_id.id != (
                company_partner.property_product_pricelist.currency_id.id):
            raise Warning(_(
                'You cannot create SO from PO because '
                'sale price list currency is different than '
                'purchase price list currency.'))

        # create the SO and generate its lines from the PO lines
        SaleOrderLine = self.pool['sale.order.line']
        # read it as sudo, because inter-compagny user
        # can not have the access right on PO
        sale_order_data = self._prepare_sale_order_data(
            cr, SUPERUSER_ID, order, company_partner, company,
            order.dest_address_id and order.dest_address_id.id or False,
            context=context)
        sale_order_id = SaleOrder.create(
            cr, intercompany_uid, sale_order_data, context=context)
        for line in order.order_line:
            so_line_vals = self._prepare_sale_order_line_data(
                cr, SUPERUSER_ID, line, company, sale_order_id,
                context=context)
            SaleOrderLine.create(cr, intercompany_uid, so_line_vals,
                                 context=context)

        # write supplier reference field on PO
        if not order.partner_ref:
            sale_order = SaleOrder.browse(
                cr, intercompany_uid, sale_order_id, context=context)
            order.write({'partner_ref': sale_order.name})

        # Validation of sale order
        if company.auto_validation:
            wf_service = netsvc.LocalService('workflow')
            wf_service.trg_validate(intercompany_uid, 'sale.order',
                                    sale_order_id, 'order_confirm', cr)
        return sale_order_id

    def _prepare_sale_order_data(self, cr, uid, order, partner, company,
                                 direct_delivery_address, context=None):
        """ Generate the Sale Order values from the PO
            :param order : the PO
            :rtype order : purchase.order record
            :param partner : the partner reprenseting the company
            :rtype partner : res.partner record
            :param company : the company of the created SO
            :rtype company : res.company record
            :param direct_delivery_address : the address of the SO
            :rtype direct_delivery_address : res.partner record
        """
        partner_addr = self.pool['res.partner'].address_get(
            cr, uid, [partner.id],
            adr_pref=['default', 'invoice', 'delivery', 'contact'],
            context=context)
        # take the first shop of the company
        shop_id = self.pool['sale.shop'].search(
            cr, uid, [('company_id', '=', company.id)], context=context)
        if not shop_id:
            raise Warning(_(
                'You cannot create SO from PO because '
                'there is no sale shop for %s') % company.name)
        return {
            'shop_id': shop_id[0],
            'client_order_ref': order.name,
            'partner_id': partner.id,
            'pricelist_id': partner.property_product_pricelist.id,
            'partner_invoice_id': partner_addr['invoice'],
            'date_order': order.date_order,
            'fiscal_position': (partner.property_account_position and
                                partner.property_account_position.id or False),
            'user_id': False,
            'auto_generated': True,
            'auto_purchase_order_id': order.id,
            'partner_shipping_id': (direct_delivery_address or
                                    partner_addr['delivery'])
        }

    def _prepare_sale_order_line_data(self, cr, uid, line, company, sale_id,
                                      context=None):
        """ Generate the Sale Order Line values from the PO line
            :param line : the origin Purchase Order Line
            :rtype line : purchase.order.line record
            :param company : the company of the created SO
            :rtype company : res.company record
            :param sale_id : the id of the SO
        """
        # it may not affected because of parallel company relation
        price = line.price_unit or 0.0
        taxes = line.taxes_id
        if line.product_id:
            taxes = line.product_id.taxes_id
        company_taxes = [tax_rec.id
                         for tax_rec in taxes
                         if tax_rec.company_id.id == company.id]
        return {
            'name': line.product_id and line.product_id.name or line.name,
            'order_id': sale_id,
            'product_uom_qty': line.product_qty,
            'product_id': line.product_id and line.product_id.id or False,
            'product_uom': (line.product_id and line.product_id.uom_id.id or
                            line.product_uom.id),
            'price_unit': price,
            'delay': line.product_id and line.product_id.sale_delay or 0.0,
            'company_id': company.id,
            'tax_id': [(6, 0, company_taxes)],
        }
