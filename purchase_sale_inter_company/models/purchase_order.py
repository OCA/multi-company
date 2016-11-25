# -*- coding: utf-8 -*-
from openerp import api, models, _, fields
from openerp.exceptions import Warning as UserError


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    invoice_method = fields.Selection(
        selection_add=[('intercompany', 'Based on intercompany invoice')])

    @api.multi
    def wkf_confirm_order(self):
        """ Generate inter company sale order base on conditions."""
        res = super(PurchaseOrder, self).wkf_confirm_order()
        for purchase_order in self:
            # get the company from partner then trigger action of
            # intercompany relation
            company_rec = self.env['res.company']._find_company_from_partner(
                purchase_order.partner_id.id)
            if company_rec:
                purchase_order.inter_company_create_sale_order(company_rec)
        return res

    @api.multi
    def inter_company_create_sale_order(self, company):
        """ Create a Sale Order from the current PO (self)
            Note : In this method, reading the current PO is done as sudo,
            and the creation of the derived
            SO as intercompany_user, minimizing the access right required
            for the trigger user.
            :param company : the company of the created PO
            :rtype company : res.company record
        """
        self.ensure_one()
        SaleOrder = self.env['sale.order']

        # find user for creating and validation SO/PO from partner company
        intercompany_uid = (company.intercompany_user_id and
                            company.intercompany_user_id.id or False)
        if not intercompany_uid:
            raise UserError(_(
                'Provide at least one user for inter company relation for % ')
                % company.name)
        # check intercompany user access rights
        if not SaleOrder.sudo(intercompany_uid).check_access_rights(
                'create', raise_exception=False):
            raise UserError(_(
                "Inter company user of company %s doesn't have enough "
                "access rights") % company.name)

        # check intercompany product
        for purchase_line in self.order_line:
            try:
                purchase_line.product_id.sudo(intercompany_uid).read()
            except:
                raise UserError(_(
                    "You cannot create SO from PO because product '%s' "
                    "is not intercompany") % purchase_line.product_id.name)

        # Accessing to selling partner with selling user, so data like
        # property_account_position can be retrieved
        company_partner = self.env['res.partner'].sudo(
            intercompany_uid).browse(self.company_id.partner_id.id)

        # check pricelist currency should be same with PO/SO document
        if self.pricelist_id.currency_id.id != (
                company_partner.property_product_pricelist.currency_id.id):
            raise UserError(_(
                'You cannot create SO from PO because '
                'sale price list currency is different than '
                'purchase price list currency.'))

        # create the SO and generate its lines from the PO lines
        SaleOrderLine = self.env['sale.order.line']
        # read it as sudo, because inter-compagny user
        # can not have the access right on PO
        sale_order_data = self.sudo()._prepare_sale_order_data(
            self.name, company_partner, company,
            self.dest_address_id and self.dest_address_id.id or False)
        sale_order = SaleOrder.sudo(intercompany_uid).create(
            sale_order_data)
        for purchase_line in self.order_line:
            sale_line_vals = self.sudo()._prepare_sale_order_line_data(
                purchase_line, company, sale_order.id)
            SaleOrderLine.sudo(intercompany_uid).create(sale_line_vals)

        # write supplier reference field on PO
        if not self.partner_ref:
            self.partner_ref = sale_order.name

        # write invoice method field on PO
        if self.invoice_method != 'intercompany':
            self.invoice_method = 'intercompany'

        # Validation of sale order
        if company.sale_auto_validation:
            sale_order.sudo(intercompany_uid).signal_workflow('order_confirm')

    @api.multi
    def _prepare_sale_order_data(self, name, partner, company,
                                 direct_delivery_address):
        """ Generate the Sale Order values from the PO
            :param name : the origin client reference
            :rtype name : string
            :param partner : the partner reprenseting the company
            :rtype partner : res.partner record
            :param company : the company of the created SO
            :rtype company : res.company record
            :param direct_delivery_address : the address of the SO
            :rtype direct_delivery_address : res.partner record
        """
        self.ensure_one()
        partner_addr = partner.sudo().address_get(['default',
                                                   'invoice',
                                                   'delivery',
                                                   'contact'])
        # find location and warehouse, pick warehouse from company object
        warehouse = (company.warehouse_id and
                     company.warehouse_id.company_id.id == company.id and
                     company.warehouse_id or False)
        if not warehouse:
            raise UserError(_(
                'Configure correct warehouse for company(%s) from '
                'Menu: Settings/companies/companies' % (company.name)))
        return {
            'name': (
                self.env['ir.sequence'].sudo().next_by_code('sale.order') or
                '/'
            ),
            'company_id': company.id,
            'client_order_ref': name,
            'partner_id': partner.id,
            'warehouse_id': warehouse.id,
            'pricelist_id': partner.property_product_pricelist.id,
            'partner_invoice_id': partner_addr['invoice'],
            'date_order': self.date_order,
            'fiscal_position': (partner.property_account_position and
                                partner.property_account_position.id or False),
            'user_id': False,
            'auto_generated': True,
            'auto_purchase_order_id': self.id,
            'partner_shipping_id': (direct_delivery_address or
                                    partner_addr['delivery'])
        }

    @api.model
    def _prepare_sale_order_line_data(self, purchase_line, company, sale_id):
        """ Generate the Sale Order Line values from the PO line
            :param line : the origin Purchase Order Line
            :rtype line : purchase.order.line record
            :param company : the company of the created SO
            :rtype company : res.company record
            :param sale_id : the id of the SO
        """
        # it may not affected because of parallel company relation
        price = purchase_line.price_unit or 0.0
        taxes = purchase_line.taxes_id
        product = None
        if purchase_line.product_id:
            # make a new browse otherwise line._uid keeps the purchasing
            # company's user and can't see the selling company's taxes
            product = self.env['product.product'].browse(
                purchase_line.product_id.id)
            taxes = product.taxes_id
        company_taxes = [tax_rec.id
                         for tax_rec in taxes
                         if tax_rec.company_id.id == company.id]
        return {
            'name': purchase_line.name,
            'order_id': sale_id,
            'product_uom_qty': purchase_line.product_qty,
            'product_id': product and product.id or False,
            'product_uom': (product and product.uom_id.id or
                            purchase_line.product_uom.id),
            'price_unit': price,
            'delay': product and product.sale_delay or 0.0,
            'company_id': company.id,
            'tax_id': [(6, 0, company_taxes)],
            'auto_purchase_line_id': purchase_line.id
        }

    @api.multi
    def action_cancel(self):
        for purchase in self:
            company = self.env['res.company']._find_company_from_partner(
                self.partner_id.id)
            intercompany_uid = company.intercompany_user_id.id
            for sale_order in self.env['sale.order'].sudo(
                intercompany_uid).search([
                    ('auto_purchase_order_id', '=', self.id)]):
                sale_order.action_cancel()
            res = super(PurchaseOrder, self).action_cancel()
            if self.invoice_method == 'intercompany':
                self.invoice_method = 'order'
            if self.partner_ref:
                self.partner_ref = ''
        return res
