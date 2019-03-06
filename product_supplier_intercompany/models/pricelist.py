# coding: utf-8
# © 2019 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models, fields
from odoo.exceptions import Warning as UserError, ValidationError


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    is_intercompany_supplier = fields.Boolean(
        inverse="_inverse_intercompany_supplier", default=False
    )

    generated_supplierinfo_ids = fields.One2many(
        comodel_name="product.supplierinfo",
        inverse_name="intercompany_pricelist_id",
    )

    @api.constrains("company_id", "is_intercompany_supplier")
    def _check_required_company_for_intercompany(self):
        for record in self:
            if record.is_intercompany_supplier and not record.company_id:
                raise ValidationError(
                    _("The company is required for intercompany pricelist")
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
            if not self.company_id:
                raise UserError(
                    _("Intercompany pricelist must belong to a company")
                )
            self.item_ids._init_supplier_info()

    def _unactive_intercompany(self):
        self.ensure_one()
        self.sudo().with_context(automatic_intercompany_sync=True).mapped(
            "generated_supplierinfo_ids"
        ).unlink()


class ProductPricelistItem(models.Model):

    _inherit = "product.pricelist.item"

    @api.multi
    def _add_product_to_synchronize(self, todo):
        for record in self:
            pricelist = record.pricelist_id
            if not pricelist.is_intercompany_supplier:
                continue
            if pricelist not in todo:
                todo[pricelist] = {
                    "products": self.env["product.product"].browse(False),
                    "templates": self.env["product.template"].browse(False),
                }
            if record.product_id:
                todo[pricelist]["products"] |= record.product_id
            elif record.product_tmpl_id:
                todo[pricelist]["templates"] |= record.product_tmpl_id
            else:
                raise UserError(
                    _("This pricelist item type is not supported yet.")
                )

    def _process_product_to_synchronize(self, todo):
        for pricelist, vals in todo.items():
            vals["templates"]._synchronise_supplier_info(pricelists=pricelist)
            vals["products"]._synchronise_supplier_info(pricelists=pricelist)

    def _init_supplier_info(self):
        todo = {}
        self._add_product_to_synchronize(todo)
        self._process_product_to_synchronize(todo)

    @api.model
    def create(self, vals):
        record = super(ProductPricelistItem, self).create(vals)
        record._init_supplier_info()
        return record

    @api.multi
    def write(self, vals):
        todo = {}
        # we complete the todo before and after the write
        # as some product can be remove from the pricelist item
        self._add_product_to_synchronize(todo)
        super(ProductPricelistItem, self).write(vals)
        self._add_product_to_synchronize(todo)
        self._process_product_to_synchronize(todo)
        return True

    @api.multi
    def unlink(self):
        todo = {}
        self._add_product_to_synchronize(todo)
        super(ProductPricelistItem, self).unlink()
        self._process_product_to_synchronize(todo)
        return True
