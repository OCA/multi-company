To propagate taxes in one product:

#. User must have group Full Accounting Features (account.group_account_user)
#. Go to Invoicing > Customers > Products.
#. Create a new product and save it.
#. Switching user company you will see that the product has the default taxes
   for all the companies.
#. Change tax in a existing product
#. If Odoo detects divergent taxes across companies, you will see a "Propagate Taxes" button.
#. Click "Propagate Taxes" button
#. Switching user company you will see that the product has the same taxes
   for all the companies.

To propagate taxes in mass:

#. User must have group Full Accounting Features (account.group_account_user)
#. Open products list view.
#. *Filters > Add custom filter > Has divergent cross-company taxes > is true > Apply*.
#. Select all products that you want to change.
#. *Action > Propagate Taxes*.
