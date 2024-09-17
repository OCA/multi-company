- go to Sales > Product > Pricelist and set a Company in a pricelist

- flag "Is Intercompany Supplier" is now visible; if enabled, a supplierinfo  will be created for each product:

1) which has an applicable pricelist line

2) where "Can be sold" and "Can be purchased" is set

- a supplierinfo will be created automatically for each new created product for which conditions above are verified

- the supplierinfo will be updated when pricelist or product is updated

- note: supplierinfo is not visible when using the same Company as the one set in "Is Intercompany Supplier" pricelist, unless technical group "Access to all supplier info" is enabled in user.
