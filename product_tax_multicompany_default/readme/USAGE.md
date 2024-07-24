To propagate taxes in one product:

1.  User must have group Full Accounting Features
    (account.group_account_user)
2.  Go to Invoicing \> Customers \> Products.
3.  Create a new product and save it.
4.  Switching user company you will see that the product has the default
    taxes for all the companies.
5.  Change tax in a existing product
6.  If Odoo detects divergent taxes across companies, you will see a
    "Propagate Taxes" button.
7.  Click "Propagate Taxes" button
8.  Switching user company you will see that the product has the same
    taxes for all the companies.

To propagate taxes in mass:

1.  User must have group Full Accounting Features
    (account.group_account_user)
2.  Open products list view.
3.  *Filters \> Add custom filter \> Has divergent cross-company taxes
    \> is true \> Apply*.
4.  Select all products that you want to change.
5.  *Action \> Propagate Taxes*.
