# coding: utf-8
# © 2019 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models, fields


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    is_intercompany_supplier = fields.Boolean(
        inverse='_inverse_intercompany_supplier')

    generated_supplierinfo_ids = fields.One2many(
        comodel_name='product.supplierinfo',
        inverse_name='intercompany_pricelist_id',
        )

    def _inverse_intercompany_supplier(self):
        for record in self:
            if record.is_intercompany_supplier:
                record._active_intercompany()
            else:
                record._unactive_intercompany()

    def _active_intercompany(self):
        self.ensure_one()
        if self.is_intercompany_supplier:
            if len(self.version_id) > 1:
                raise UserError(
                    _('Only one version is supported for'
                      'intercompany pricelist'))
            self.version_id.items_id._init_supplier_info()

    def _unactive_intercompany(self):
        self.ensure_one()
        self.sudo().with_context(
            automatic_intercompany_sync=True).mapped(
            'generated_supplierinfo_ids').unlink()

    @api.multi
    def _sync_all_supplierinfo(self, templates, variants):
        for record in self:
            if templates:
                templates._synchronise_supplier_info(pricelists=record)
            if variants:
                variants._synchronise_supplier_info(pricelists=record)


class ProductPricelistItem(models.Model):

    _inherit = 'product.pricelist.item'

    @api.multi
    def _init_supplier_info(self):
        for record in self:
            pricelist = record.price_version_id.pricelist_id
            templates, variants = record._get_products_to_synchronise()
            pricelist._sync_all_supplierinfo(templates, variants)

    @api.multi
    def _get_products_to_synchronise(self):
        '''
        returns (templates, products) always as recordset (can be empty)
        '''
        for record in self:
            if self.product_id:
                return self.env['product.template'].browse(), self.product_id
            elif self.product_tmpl_id:
                return (self.product_tmpl_id,
                        self.env['product.product'].browse())
            else:
                raise Exception(
                    'This pricelist item type is not supported yet.')

    @api.multi
    def write(self, vals):
        for record in self:
            pricelist = record.price_version_id.pricelist_id
            if pricelist.is_intercompany_supplier:
                templates, variants = record._get_products_to_synchronise()
                super(ProductPricelistItem, self).write(vals)
                new_to_sync = record._get_products_to_synchronise()
                templates |= new_to_sync[0]
                variants |= new_to_sync[1]
                pricelist._sync_all_supplierinfo(templates, variants)

    @api.multi
    def unlink(self):
        for record in self:
            pricelist = record.price_version_id.pricelist_id
            if pricelist.is_intercompany_supplier:
                templates, variants = record._get_products_to_synchronise()
                super(ProductPricelistItem, self).unlink()
                pricelist._sync_all_supplierinfo(templates, variants)
