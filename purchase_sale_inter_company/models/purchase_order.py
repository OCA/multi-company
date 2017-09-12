# -*- coding: utf-8 -*-
# © 2013-Today Odoo SA
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

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
            dest_company = self.env['res.company']._find_company_from_partner(
                purchase_order.partner_id.id)
            if dest_company:
                purchase_order.sudo().\
                    with_context(force_company=dest_company.id).\
                    _inter_company_create_sale_order(dest_company.id)
        return res

    @api.multi
    def _get_user_domain(self, dest_company):
        self.ensure_one()
        group_purchase_user = self.env.ref('purchase.group_purchase_user')
        return [
            ('id', '!=', 1),
            ('company_id', '=', dest_company.id),
            ('id', 'in', group_purchase_user.users.ids),
            ]

    @api.multi
    def _check_intercompany_product(self, dest_company):
        domain = self._get_user_domain(dest_company)
        dest_user = self.env['res.users'].search(domain, limit=1)
        if dest_user:
            for purchase_line in self.order_line:
                try:
                    purchase_line.product_id.sudo(dest_user).read()
                except:
                    raise UserError(_(
                        "You cannot create SO from PO because product '%s' "
                        "is not intercompany") % purchase_line.product_id.name)

    @api.multi
    def _inter_company_create_sale_order(self, dest_company_id):
        """ Create a Sale Order from the current PO (self)
            Note : In this method, should be call in sudo with the propert
            destination company in the context
            :param company : the company of the created PO
            :rtype company : res.company record
        """
        self.ensure_one()
        dest_company = self.env['res.company'].browse(dest_company_id)
        # check intercompany product
        self._check_intercompany_product(dest_company)
        # Accessing to selling partner with selling user, so data like
        # property_account_position can be retrieved
        company_partner = self.company_id.partner_id
        # check pricelist currency should be same with PO/SO document
        if self.pricelist_id.currency_id.id != (
                company_partner.property_product_pricelist.currency_id.id):
            raise UserError(_(
                'You cannot create SO from PO because '
                'sale price list currency is different from '
                'purchase price list currency.'))
        # create the SO and generate its lines from the PO lines
        sale_order_data = self._prepare_sale_order_data(
            self.name, company_partner, dest_company,
            self.dest_address_id and self.dest_address_id.id or False)
        sale_order = self.env['sale.order'].create(sale_order_data)
        for purchase_line in self.order_line:
            sale_line_data = self._prepare_sale_order_line_data(
                purchase_line, dest_company, sale_order)
            self.env['sale.order.line'].create(sale_line_data)
        # write supplier reference field on PO
        if not self.partner_ref:
            self.partner_ref = sale_order.name
        # write invoice method field on PO
        if self.invoice_method != 'intercompany':
            self.invoice_method = 'intercompany'
        # Validation of sale order
        if dest_company.sale_auto_validation:
            sale_order.signal_workflow('order_confirm')

    @api.multi
    def _prepare_sale_order_data(self, name, partner, dest_company,
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
        partner_addr = partner.address_get(['default',
                                            'invoice',
                                            'delivery',
                                            'contact'])
        # find location and warehouse, pick warehouse from company object
        warehouse = (
            dest_company.warehouse_id and
            dest_company.warehouse_id.company_id.id == dest_company.id and
            dest_company.warehouse_id or False)
        if not warehouse:
            raise UserError(_(
                'Configure correct warehouse for company (%s) in '
                'Menu: Settings/companies/companies' % (dest_company.name)))
        partner_shipping_id = (
            self.picking_type_id.warehouse_id and
            self.picking_type_id.warehouse_id.partner_id and
            self.picking_type_id.warehouse_id.partner_id.id or False)
        return {
            'name': (
                self.env['ir.sequence'].next_by_code('sale.order') or '/'
            ),
            'company_id': dest_company.id,
            'client_order_ref': name,
            'partner_id': partner.id,
            'warehouse_id': warehouse.id,
            'pricelist_id': partner.property_product_pricelist.id,
            'partner_invoice_id': partner_addr['invoice'],
            'date_order': self.date_order,
            'fiscal_position': (partner.property_account_position and
                                partner.property_account_position.id or False),
            'user_id': False,
            'auto_purchase_order_id': self.id,
            'partner_shipping_id': (direct_delivery_address or
                                    partner_shipping_id or
                                    partner_addr['delivery']),
            'note': self.notes
        }

    @api.model
    def _prepare_sale_order_line_data(
            self, purchase_line, dest_company, sale_order):
        """ Generate the Sale Order Line values from the PO line
            :param line : the origin Purchase Order Line
            :rtype line : purchase.order.line record
            :param company : the company of the created SO
            :rtype company : res.company record
            :param sale_order : the Sale Order
        """
        context = self._context.copy()
        context['company_id'] = dest_company.id
        # get sale line data from product onchange
        sale_line_obj = self.env['sale.order.line'].browse(False)
        sale_line_data = sale_line_obj.with_context(
            context).product_id_change_with_wh(
                pricelist=sale_order.pricelist_id.id,
                product=(purchase_line.product_id and
                         purchase_line.product_id.id or False),
                qty=purchase_line.product_qty,
                uom=(purchase_line.product_id and
                     purchase_line.product_id.uom_id.id or False),
                qty_uos=0,
                uos=False,
                name='',
                partner_id=sale_order.partner_id.id,
                lang=False,
                update_tax=True,
                date_order=sale_order.date_order,
                packaging=False,
                fiscal_position=sale_order.fiscal_position.id,
                flag=False,
                warehouse_id=sale_order.warehouse_id.id)
        sale_line_data['value']['product_id'] = (
            purchase_line.product_id and purchase_line.product_id.id or
            False)
        sale_line_data['value']['order_id'] = sale_order.id
        sale_line_data['value']['delay'] = (purchase_line.product_id and
                                            purchase_line.product_id.
                                            sale_delay or 0.0)
        sale_line_data['value']['company_id'] = dest_company.id
        sale_line_data['value']['product_uom_qty'] = (purchase_line.
                                                      product_qty)
        sale_line_data['value']['product_uom'] = (
            purchase_line.product_id and
            purchase_line.product_id.uom_id.id or
            purchase_line.product_uom.id)
        if sale_line_data['value'].get('tax_id'):
            sale_line_data['value']['tax_id'] = ([
                [6, 0, sale_line_data['value']['tax_id']]])
        sale_line_data['value']['auto_purchase_line_id'] = purchase_line.id
        return sale_line_data['value']

    @api.multi
    def action_cancel(self):
        for purchase in self:
            for sale_order in self.env['sale.order'].sudo().search([
                    ('auto_purchase_order_id', '=', purchase.id)]):
                sale_order.action_cancel()
            res = super(PurchaseOrder, purchase).action_cancel()
            if purchase.invoice_method == 'intercompany':
                purchase.invoice_method = 'order'
            if purchase.partner_ref:
                purchase.partner_ref = ''
        return res
