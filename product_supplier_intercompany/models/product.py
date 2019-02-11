# coding: utf-8
# © 2019 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class ProductIntercompanySupplierMixin(models.AbstractModel):
    _name = 'product.intercompany.supplier.mixin'

    def _synchronise_supplier_info(self, pricelists=None):
        if not pricelists:
            pricelists = self.env['product.pricelist'].search(
                [('is_intercompany_supplier', '=', True)])

        for pricelist in pricelists:
            # chaque pricelist est mise dans le context pour avoir
            # le bon prix de vente (compatible v8 à v12)
            partner = pricelist.company_id.partner_id
            for record in self.with_context(
                    pricelist=pricelist.id, partner_id=partner.id,
                    automatic_intercompany_sync=True):
                supplier = record._get_intercompany_supplier_info()
                if record.has_intercompany_price():
                    vals = record._prepare_intercompany_supplier_info()
                    if supplier:
                        supplier.pricelist_ids.unlink()
                        supplier.write(vals)
                    else:
                        self.env['product.supplierinfo'].create(vals)
                elif supplier:
                    supplier.unlink()

    def has_intercompany_price(self):
        raise NotImplementedError

    def _get_intercompany_supplier_info(self):
        raise NotImplementedError

    def _prepare_intercompany_supplier_info(self):
        for record in self:
            return {
                'intercompany_pricelist_id': record._context.get('pricelist'),
                'name': record._context.get('partner_id'),
                'pricelist_ids': [
                    (0, 0, {'min_quantity': 1, 'price': record.price})]
            }


class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = ['product.product', 'product.intercompany.supplier.mixin']

    def _get_intercompany_supplier_info(self):
        self.ensure_one()
        return self.seller_ids.search([
            ('intercompany_pricelist_id', '=', self._context.get('pricelist')),
            ('product_id', '=', self.id)])

    def _prepare_intercompany_supplier_info(self):
        for record in self:
            vals = super(
                ProductProduct, self)._prepare_intercompany_supplier_info()
            vals.update({
                'product_id': record.id,
                'product_tmpl_id': record.product_tmpl_id.id,
            })
            return vals

    def has_intercompany_price(self):
        self.ensure_one()
        if self.env['product.pricelist.item'].search([
                ('price_version_id.pricelist_id', '=',
                    self._context.get('pricelist')),
                ('product_id', '=', self.id)]):
            return True


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'product.intercompany.supplier.mixin']

    def _get_intercompany_supplier_info(self):
        self.ensure_one()
        return self.seller_ids.search([
            ('intercompany_pricelist_id', '=', self._context.get('pricelist')),
            ('product_id', '=', False)])

    def _prepare_intercompany_supplier_info(self):
        for record in self:
            vals = super(
                ProductTemplate, self)._prepare_intercompany_supplier_info()
            vals.update({
                'product_tmpl_id': record.id,
            })
            return vals

    def has_intercompany_price(self):
        self.ensure_one()
        if self.env['product.pricelist.item'].search([
                ('price_version_id.pricelist_id', '=',
                    self._context.get('pricelist')),
                ('product_tmpl_id', '=', self.id),
                ('product_id', '=', False)]):
            return True


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    intercompany_pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        inverse_name='generated_supplier_info_ids')

    def _check_intercompany_supplier(self):
        self.ensure_one()
        if (not self._context.get('automatic_intercompany_sync') and
                self.mapped('intercompany_pricelist_id')):
            raise Exception(
                'This supplier info is managed by an intercompany pricelist')

    def write(self, vals):
        for record in self:
            record._check_intercompany_supplier()
        super(ProductSupplierinfo, self).write(vals)

    def create(self, vals):
        for record in self:
            record._check_intercompany_supplier()
        super(ProductSupplierinfo, self).create(vals)

    def unlink(self):
        for record in self:
            record._check_intercompany_supplier()
        super(ProductSupplierinfo, self).unlink()
