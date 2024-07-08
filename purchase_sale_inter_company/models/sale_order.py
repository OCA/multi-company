# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    auto_purchase_order_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Source Purchase Order',
        readonly=True,
        copy=False,
    )

    def assert_intercompany_prices_equal(self):
        """Check if the prices of both orders are the same"""
        unequal_line = []
        for so in self:
            for line in so.sudo().order_line:
                if not line.auto_purchase_line_id:
                    continue
                if not so.currency_id.compare_amounts(
                   line.price_unit, line.auto_purchase_line_id.price_unit):
                    continue
                po_line_prod = (
                    line.product_id.default_code or line.product_id.name)
                so_line_prod = (
                    line.auto_purchase_line_id.product_id.default_code
                    or line.auto_purchase_line_id.product_id.name)
                unequal_line.append(
                    _("PO line %s with price %s is not equal to SO "
                      "line %s with price %s \n"
                      ) % (po_line_prod,
                           line.auto_purchase_line_id.price_unit,
                           so_line_prod,
                           line.price_unit))

        if unequal_line:
            raise UserError(
                _('Error. The following lines do not match on'
                  ' the remote order: %s') % "\n".join(unequal_line))

    @api.multi
    def action_confirm(self):
        for order in self.filtered('auto_purchase_order_id'):
            po_company = order.sudo().auto_purchase_order_id.company_id
            if not po_company.intercompany_overwrite_purchase_price:
                order.assert_intercompany_prices_equal()
            else:
                for line in order.order_line.sudo():
                    if line.auto_purchase_line_id:
                        line.auto_purchase_line_id.price_unit = line.price_unit
        res = super(SaleOrder, self).action_confirm()
        for sale_order in self.sudo():
            # Do not consider SO created from intercompany PO
            dest_company = sale_order.partner_id.ref_company_ids
            if not sale_order.auto_purchase_order_id:
                if dest_company and dest_company.po_from_so:
                    sale_order.with_context(
                        force_company=dest_company.id
                    )._inter_company_create_purchase_order(dest_company)
            if sale_order.auto_purchase_order_id and dest_company \
                    and dest_company.sync_picking:
                pickings = sale_order.picking_ids
                po_company = sale_order.sudo().auto_purchase_order_id.company_id
                purchase_picking = sale_order.auto_purchase_order_id.sudo(
                    po_company.intercompany_user_id.id).picking_ids

                if len(pickings) == len(purchase_picking) == 1:
                    # thus they have the same moves and move lines with same quantities
                    purchase_picking.write({'intercompany_picking_id': pickings.id})
                    pickings.write({'intercompany_picking_id': purchase_picking.id})
                if len(pickings) > 1 and len(purchase_picking) == 1:
                    # If there are several pickings in the sale order and one
                    # in the purchase order, then split the receipt
                    # thus we need to recreate new moves and moves lines, as they differ
                    purchase_moves = purchase_picking.move_ids_without_package
                    purchase_move_lines = purchase_picking.move_line_ids_without_package
                    new_pickings = self.env["stock.picking"].sudo(
                        po_company.intercompany_user_id.id)
                    for i, pick in enumerate(pickings):
                        moves = pick.move_ids_without_package
                        new_moves = self.env["stock.move"].sudo(
                            po_company.intercompany_user_id.id)
                        new_move_lines = self.env["stock.move.line"].sudo(
                            po_company.intercompany_user_id.id)
                        for move in moves:
                            purchase_move = purchase_moves.filtered(
                                lambda m: m.product_id.id == move.product_id.id)[:1]
                            new_move = purchase_move.sudo(
                                po_company.intercompany_user_id.id).copy({
                                    'picking_id':
                                        purchase_picking.id if i == 0 else False,
                                    "name": move.name,
                                    "product_uom_qty": move.product_uom_qty,
                                    "product_uom": move.product_uom.id,
                                    "price_unit": -move.price_unit,
                                    "note": move.note,
                                    "create_date": move.create_date,
                                    "date": move.date,
                                    "date_expected": move.date_expected,
                                    "state": move.state,
                                })
                            new_move._update_extra_data_in_move(move)
                            new_moves |= new_move
                            for move_line in move.move_line_ids.filtered(
                                lambda l: l.package_level_id and
                                not l.picking_type_entire_packs
                            ):
                                purchase_move_line = purchase_move_lines.filtered(
                                    lambda l:
                                    l.product_id.id == move_line.product_id.id)[:1]
                                new_move_line = purchase_move_line.sudo(
                                    po_company.intercompany_user_id.id).copy({
                                        'picking_id': purchase_picking.id
                                        if i == 0 else False,
                                        'move_id': new_move.id,
                                        "product_uom_qty": move_line.product_uom_qty,
                                        "product_uom_id": move_line.product_uom_id.id,
                                        "create_date": move_line.create_date,
                                        "date": move_line.date,
                                        "state": move_line.state,
                                    })
                                new_move_line._update_extra_data_in_move_line(move_line)
                                new_move_lines |= new_move_line
                        if i == 0:
                            purchase_picking.sudo(
                                purchase_picking.company_id.intercompany_user_id.id
                            ).write({
                                'intercompany_picking_id': pick.id,
                                'note': pick.note,
                                "create_date": pick.create_date,
                                "state": pick.state,
                            })
                            new_pick = purchase_picking
                        else:
                            new_pick = purchase_picking.sudo(
                                po_company.intercompany_user_id.id).copy({
                                    'move_ids_without_package': [
                                        (6, False, new_moves.ids)],
                                    'move_line_ids_without_package': [
                                        (6, False, new_move_lines.ids)],
                                    'intercompany_picking_id': pick.id,
                                    'note': pick.note,
                                    "create_date": pick.create_date,
                                    "state": pick.state,
                                })
                            new_pick._update_extra_data_in_picking(pick)
                        pick.write({'intercompany_picking_id': new_pick.id})
                        new_pickings |= new_pick
                    purchase_move_lines.unlink()
                    purchase_moves._action_cancel()
                    purchase_moves.unlink()
                    purchase_picking._update_extra_data_in_picking(pickings[:1])
                    new_pickings.action_assign()

        return res

    @api.multi
    def _get_user_domain(self, dest_company):
        self.ensure_one()
        group_sale_user = self.env.ref('sales_team.group_sale_salesman')
        return [
            ('id', '!=', 1),
            ('company_id', '=', dest_company.id),
            ('id', 'in', group_sale_user.users.ids),
        ]

    @api.multi
    def _check_intercompany_product(self, dest_company):
        domain = self._get_user_domain(dest_company)
        dest_user = self.env['res.users'].search(domain, limit=1)
        if dest_user:
            for sale_line in self.order_line:
                try:
                    sale_line.product_id.sudo(dest_user).read(
                        ['default_code'])
                except Exception:
                    raise UserError(_(
                        "You cannot create PO from SO because product '%s' "
                        "is not intercompany") % sale_line.product_id.name)

    @api.multi
    def _inter_company_create_purchase_order(self, dest_company):
        """ Create a Purchase Order from the current SO (self)
            Note : In this method, reading the current SO is done as sudo,
            and the creation of the derived
            PO as intercompany_user, minimizing the access right required
            for the trigger user.
            :param dest_company : the company of the created SO
            :rtype dest_company : res.company record
        """
        self.ensure_one()
        intercompany_user = dest_company.intercompany_user_id
        if intercompany_user.company_id != dest_company:
            intercompany_user.company_id = dest_company
        self._check_intercompany_product(dest_company)
        company_partner = self.company_id.partner_id
        purchase_order_data = self._prepare_purchase_order_data(
            self.name, company_partner, dest_company)
        purchase_order = self.env['purchase.order'].sudo(
            intercompany_user.id).create(purchase_order_data)
        for sale_line in self.order_line:
            purchase_line_data = self._prepare_purchase_order_line_data(
                sale_line, purchase_order)
            self.env['purchase.order.line'].sudo(
                intercompany_user.id).create(purchase_line_data)
        if not self.name:
            self.name = purchase_order.partner_ref
        # Validation of sale order
        if dest_company.purchase_auto_validation:
            purchase_order.sudo(intercompany_user.id).button_approve()

    @api.multi
    def _prepare_purchase_order_data(self, name, partner, dest_company):
        """ Generate the Purchase Order values from the SO
            :param name : the origin client reference
            :rtype name : string
            :param partner : the partner reprenseting the company
            :rtype partner : res.partner record
            :param dest_company : the company of the created PO
            :rtype dest_company : res.company record
        """
        self.ensure_one()
        new_order = self.env['purchase.order'].new({
            'company_id': dest_company.id,
            'partner_ref': name,
            'partner_id': partner.id,
            'date_order': self.date_order,
            'auto_sale_order_id': self.id,
        })
        for onchange_method in new_order._onchange_methods['partner_id']:
            onchange_method(new_order)
        new_order.user_id = False
        if self.note:
            new_order.notes = self.note
        if 'picking_type_id' in new_order:
            new_order.picking_type_id = (
                dest_company.po_picking_type_id.warehouse_id.company_id ==
                dest_company and dest_company.po_picking_type_id or False)
        return new_order._convert_to_write(new_order._cache)

    @api.model
    def _prepare_purchase_order_line_data(
            self, sale_line, purchase_order):
        """ Generate the Purchase Order Line values from the SO line
            :param sale_line : the origin Sale Order Line
            :rtype sale_line : sale.order.line record
            :param purchase_order : the Purchase Order
        """
        new_line = self.env['purchase.order.line'].new({
            'order_id': purchase_order.id,
            'product_id': sale_line.product_id.id,
            'auto_sale_line_id': sale_line.id,
        })
        for onchange_method in new_line._onchange_methods['product_id']:
            onchange_method(new_line)
        new_line.product_uom = sale_line.product_uom.id
        new_line.product_qty = sale_line.product_uom_qty
        new_line.price_unit = sale_line.price_unit
        return new_line._convert_to_write(new_line._cache)

    @api.multi
    def action_cancel(self):
        purchase_orders = self.env['purchase.order'].sudo().search([
            ('auto_sale_order_id', 'in', self.ids)])
        for po in purchase_orders:
            if po.state not in ['draft', 'sent', 'cancel']:
                raise UserError(_("You can't cancel an order that is %s")
                                % po.state)
        if purchase_orders:
            purchase_orders.button_cancel()
        return super().action_cancel()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    auto_purchase_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string='Source Purchase Order Line',
        readonly=True,
        copy=False,
    )
