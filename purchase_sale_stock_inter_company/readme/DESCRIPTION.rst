This module considers the propagation of the warehouse into the sale orders.

When Company A sends a product tracked by lot or serial number, a new lot/serial number with the same name is created in Company B to match it, if one doesn't already exist.

This module is a glue module and is auto installed if `purchase_sale_inter_company`, `sale_stock` and `purchase_stock` modules are installed.
Full purpose description can be found in `purchase_sale_inter_company`.
