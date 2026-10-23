When both `purchase_sale_stock_inter_company` and `stock_intercompany`
are installed, validating transfers between inter-company partners would
normally trigger duplicate pickings — `stock_intercompany` and
`purchase_sale_stock_inter_company` each reacting independently to the
same event.

This glue module prevents all such duplications by delegating to the
right module depending on whether a PO/SO document pair is managing the
flow:

**LR direction (delivery → receipt):** When a delivery is linked to a
Sale Order generated from an inter-company Purchase Order
(`_is_intercompany_delivery()` is True),
`purchase_sale_stock_inter_company` manages the receipt in the
destination company through the PO/SO pair. `stock_intercompany` is
instructed to skip counterpart creation for that delivery.

**RL direction (receipt → delivery):** When a receipt picking is linked
to a Purchase Order that has a mirror Sale Order
(`intercompany_sale_order_id` is set),
`purchase_sale_stock_inter_company` owns that relationship.
`stock_intercompany` is instructed to skip delivery counterpart creation
for that receipt, both via the manual *Create Counterpart* button and
via the scheduled action.

When no inter-company PO/SO pair exists for a given transfer,
`stock_intercompany` behaves normally and creates counterpart pickings
as configured.
