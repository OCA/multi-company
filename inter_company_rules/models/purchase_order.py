# -*- coding: utf-8 -*-
from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    auto_generated = fields.Boolean(string='Auto Generated Purchase Order',
                                    copy=False)
    auto_sale_order_id = fields.Many2one('sale.order',
                                         string='Source Sale Order',
                                         readonly=True, copy=False)

    @api.multi
    def button_confirm(self):
        """ Generate inter company sale order base on conditions."""
        res = super(PurchaseOrder, self).button_confirm()
        for order in self:
            # get the company from partner then trigger action of
            # intercompany relation
            company_rec = self.env['res.company']._find_company_from_partner(
                order.partner_id.id)
            if company_rec and company_rec.so_from_po and (
                    not order.auto_generated):
                order.inter_company_create_sale_order(company_rec)
        return res

    @api.one
    def inter_company_create_sale_order(self, company):
        """ Create a Sale Order from the current PO (self)
            Note : In this method, reading the current PO is done as sudo,
            and the creation of the derived
            SO as intercompany_user, minimizing the access right required
            for the trigger user.
            :param company : the company of the created PO
            :rtype company : res.company record
        """
        SaleOrder = self.env['sale.order']

        # find user for creating and validation SO/PO from partner company
        intercompany_uid = (company.intercompany_user_id and
                            company.intercompany_user_id.id or False)
        if not intercompany_uid:
            raise UserError(_(
                'Provide at least one user for inter company relation for %s')
                % company.name)
        # check intercompany user access rights
        if not SaleOrder.sudo(intercompany_uid).check_access_rights(
                'create', raise_exception=False):
            raise UserError(_(
                "Inter company user of company %s doesn't have enough "
                "access rights") % company.name)

        # Accessing to selling partner with selling user, so data like
        # property_account_position can be retrieved
        company_partner = self.env['res.partner'].sudo(
            intercompany_uid).browse(self.company_id.partner_id.id)

        # check pricelist currency should be same with SO/PO document
        if self.currency_id.id != (
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
            sale_order_data[0])
        for line in self.order_line:
            so_line_vals = self.sudo()._prepare_sale_order_line_data(
                line, company, sale_order.id)
            SaleOrderLine.sudo(intercompany_uid).create(so_line_vals)

        # write supplier reference field on PO
        if not self.partner_ref:
            self.partner_ref = sale_order.name

        # Validation of sale order
        if company.auto_validation:
            sale_order.sudo(intercompany_uid).action_confirm()

    @api.one
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
        partner_addr = partner.sudo().address_get(['default',
                                                   'invoice',
                                                   'delivery',
                                                   'contact'])
        return {
            'name': (
                self.env['ir.sequence'].sudo().next_by_code('sale.order') or
                '/'
            ),
            'company_id': company.id,
            'client_order_ref': name,
            'partner_id': partner.id,
            'pricelist_id': partner.property_product_pricelist.id,
            'partner_invoice_id': partner_addr['invoice'],
            'date_order': self.date_order,
            'fiscal_position_id': partner.property_account_position_id.id,
            'user_id': False,
            'auto_generated': True,
            'auto_purchase_order_id': self.id,
            'partner_shipping_id': (direct_delivery_address or
                                    partner_addr['delivery']),
            'warehouse_id': company.warehouse_id.filtered(
                lambda x: x.company_id == company).id,
        }

    @api.model
    def _prepare_sale_order_line_data(self, line, company, sale_id):
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
        product = None
        if line.product_id:
            # make a new browse otherwise line._uid keeps the purchasing
            # company's user and can't see the selling company's taxes
            product = self.env['product.product'].browse(line.product_id.id)
            taxes = product.taxes_id
        company_taxes = [tax_rec.id
                         for tax_rec in taxes
                         if tax_rec.company_id.id == company.id]
        return {
            'name': line.name,
            'order_id': sale_id,
            'product_uom_qty': line.product_qty,
            'product_id': product and product.id or False,
            'product_uom': (product and product.uom_id.id or
                            line.product_uom.id),
            'price_unit': price,
            'customer_lead': product and product.sale_delay or 0.0,
            'company_id': company.id,
            'tax_id': [(6, 0, company_taxes)],
        }


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def do_transfer(self):
        # Only DropShip pickings
        po_picks = self.browse()
        for pick in self.filtered(
                lambda x: x.location_dest_id.usage == 'customer'):
            purchase = pick.sale_id.auto_purchase_order_id
            if not purchase:
                continue
            for operation in pick.pack_operation_product_ids:
                po_operations = purchase.sudo().picking_ids.mapped(
                        'pack_operation_product_ids').filtered(
                            lambda x: x.product_id == operation.product_id and
                            not x.processed_boolean)
                qty_done = operation.qty_done
                for po_operation in po_operations:
                    if po_operation.product_qty >= qty_done:
                        po_operation.qty_done = qty_done
                        qty_done = 0.0
                    else:
                        po_operation.qty_done = po_operation.product_qty
                        qty_done -= po_operation.product_qty
                    po_picks |= po_operation.picking_id
                if qty_done and po_operations:
                    po_operations[-1:].qty_done += qty_done
                elif not po_operations:
                    raise UserError(_('Any picking to assign units'))
                    # TODO: Create new DropShip Picking
        # Done dropship pickings
        po_self = self.with_context(
            force_company=po_picks[0].sudo().company_id.id).sudo()
        for po_pick in po_picks:
            po_self.env['stock.backorder.confirmation'].new(
                {'pick_id': po_pick.id}).process()
        return super(StockPicking, self).do_transfer()
