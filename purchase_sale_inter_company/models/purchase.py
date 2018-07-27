# -*- coding: utf-8 -*-
from odoo import api, models, _, fields
from odoo.exceptions import AccessError, UserError


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    invoice_status = fields.Selection(
        selection_add=[('intercompany', 'Based on intercompany invoice')])

    @api.multi
    def button_confirm(self):
        """ Generate inter company sale order base on conditions."""
        res = super(PurchaseOrder, self).button_confirm()
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
                    purchase_line.product_id.sudo(dest_user).read(
                        ['default_code'])
                except:
                    raise AccessError(_(
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
        # check currency should be same with PO/SO document
        if self.currency_id.id != (
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
        # write invoice status field on PO
        if self.invoice_status != 'intercompany':
            self.invoice_status = 'intercompany'
        # Validation of sale order
        if dest_company.sale_auto_validation:
            sale_order.action_confirm()

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
        partner_addr = partner.address_get(['other',
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
                'Menu: Settings/users/companies' % (dest_company.name)))
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
            'fiscal_position_id': (partner.property_account_position_id and
                                   partner.property_account_position_id.id or
                                   False),
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
        sale_line = self.env['sale.order.line'].new({
            'order_id': sale_order.id,
            'product_id': purchase_line.product_id.id,
            'product_uom_qty': purchase_line.product_qty,
            'product_uom': (purchase_line.product_uom.id or
                            purchase_line.product_id and
                            purchase_line.product_id.uom_id.id or False),
            'delay': (purchase_line.product_id and
                      purchase_line.product_id.sale_delay or 0.0),
            'company_id': dest_company.id,
            'auto_purchase_line_id': purchase_line.id
        })
        sale_line.product_id_change()
        line_values = sale_line._convert_to_write(sale_line._cache)
        return line_values

    @api.multi
    def button_cancel(self):
        sale_orders = self.env['sale.order'].sudo().search([
            ('auto_purchase_order_id', 'in', self.ids)])
        sale_orders.action_cancel()
        self.write({
            'invoice_status': 'no',
            'partner_ref': False,
        })
        return super(PurchaseOrder, self).button_cancel()
