This module is a glue module and is auto installed if
purchase_sale_inter_company, sale_stock and purchase_stock modules are
installed. Full purpose description can be found in
purchase_sale_inter_company.

In addition to the features provided by purchase_sale_inter_company, which
automatically creates inter-company Sale Orders from Purchase Orders, this module
extends the functionality by automatically validating the corresponding inter-company
receipts when the Delivery Order is confirmed. During this process, lot/serial numbers
and quantities are synchronized to ensure consistency across companies.

The configuration includes an option to specify a default Warehouse that will be
automatically assigned to Sale Orders generated from Purchase Orders addressed to
this company.

When Company A sends a product tracked by lot or serial number, a new
lot/serial number with the same name is created in Company B to match
it, if one doesn't already exist.

When Company B validates the return of an inter-company delivery, the return of
the matching receipt is created in Company A for the returned quantities and
lots, and it is validated when Company A synchronizes pickings. Odoo 20.0 has no
return wizard anymore, so this purchase return is created when the sale return is
validated. An exchange (the return of that return) is synchronized like a new
delivery.
