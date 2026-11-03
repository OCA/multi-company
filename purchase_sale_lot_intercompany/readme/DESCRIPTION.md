In some groups, the lot/serial number is a better product identifier than
the product variant (e.g. configurable products with many attributes, or
attributes that don't create variants). This identifier must be propagated
and enforced on every document: sales, purchases, stock and accounting.

This module propagates the lot/serial number set on an intercompany purchase
order line to the matching sale order line in the supplier company. Thanks to
`sale_order_lot_selection` and `stock_restrict_lot`, the supplier company has
to deliver the lot ordered by the buyer.

Lots are shared between companies: the lot of the purchase line is reused
(its company is cleared if needed) instead of being duplicated.
