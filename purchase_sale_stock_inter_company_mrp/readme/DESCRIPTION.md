This module keeps the intercompany delivery and receipt synchronized for
kit products, whether the phantom BOM is defined only on the purchase
side, only on the sale side, on both sides, or with different BOMs on
each side for the same product.

The same logic applies to returns: the returned quantities are recomputed
and synchronized on both sides.

Components and kit products cannot be tracked by lot or serial number, as
their lots cannot be mapped between possibly different BOMs.

This module is a glue module and is auto installed if
purchase_sale_stock_inter_company and mrp modules are installed. Full
purpose description can be found in purchase_sale_inter_company.
