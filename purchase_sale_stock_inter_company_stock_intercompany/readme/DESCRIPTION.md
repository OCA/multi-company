When both `purchase_sale_stock_inter_company` and `stock_intercompany`
are installed, validating a delivery to an inter-company partner would
normally trigger two separate incoming pickings in the destination
company:

- one created by `stock_intercompany` based on the partner/company
  mapping,
- one managed by `purchase_sale_stock_inter_company` through the linked
  Purchase Order / Sale Order document pair.

This glue module prevents the duplication by instructing
`stock_intercompany` to skip counterpart picking creation whenever
`purchase_sale_stock_inter_company` is already responsible for that
delivery (i.e. the delivery is linked to a Sale Order generated from an
inter-company Purchase Order).

When no inter-company PO/SO pair exists for a given delivery,
`stock_intercompany` behaves normally and creates the counterpart
picking as usual.
