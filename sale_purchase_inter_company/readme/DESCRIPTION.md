This module is useful if there are multiple companies in the same Odoo
database and those companies sell goods or services among themselves. It
allows to create a purchase order (PO) automatically in company A from a
sale order (SO) created in company B.

Imagine you have company A and company B in the same Odoo database:

- Company A sells goods or services to company B.
- Company A creates a sale order (SO) with company B as customer.
- This module automates the creation of the purchase order (PO) in
  company B with company A as seller.

This module implements the converse behaviour to module
`purchase_sale_inter_company`, from which it contains derivative code
(under the same license).
