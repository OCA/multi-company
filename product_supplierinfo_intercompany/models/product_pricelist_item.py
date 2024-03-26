# © 2019 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import Warning as UserError


class ProductPricelistItem(models.Model):

    _inherit = "product.pricelist.item"

    def _add_product_to_synchronize(self, todo):
        """formats the supplied arg:
        todo[record.pricelist]["products"|"templates"]
        """
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
            elif record.applied_on == "3_global":
                product_tmpl_ids = self.env["product.template"].search(
                    [("active", "=", True)]
                )
                todo[pricelist]["templates"] |= product_tmpl_ids
            elif record.applied_on == "2_product_category":
                product_tmpl_ids = self.env["product.template"].search(
                    [
                        ("active", "=", True),
                        ("categ_id", "child_of", record.categ_id.ids),
                    ]
                )
                todo[pricelist]["templates"] |= product_tmpl_ids
            else:
                raise UserError(
                    _(
                        "At least one pricelist item type is not supported yet."
                        " Please ensure all intercompany pricelist items are "
                        "linked to either a product template or a product "
                        "variant."
                    )
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
        record = super().create(vals)
        record._init_supplier_info()
        return record

    def write(self, vals):
        todo = {}
        # we complete the todo before and after the write
        # as some product can be remove from the pricelist item
        self._add_product_to_synchronize(todo)
        super().write(vals)
        self._add_product_to_synchronize(todo)
        self._process_product_to_synchronize(todo)
        return True

    def unlink(self):
        todo = {}
        self._add_product_to_synchronize(todo)
        super().unlink()
        self._process_product_to_synchronize(todo)
        return True
