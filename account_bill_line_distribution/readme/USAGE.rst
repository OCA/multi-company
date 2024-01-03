* Go to *Accounting > Vendors > Bills*
* Create a new bill
* Select the vendor
* Add a line:

  * Select the product and set the quantity
  * Create the distribution by adding lines with a company and its percentage

* Validate the invoice

In the current company, an additional journal entry is created in the Due
To/Due From journal:

+---------------+-----------+--------+--------+
| Account       | Partner   | Debit  | Credit |
+===============+===========+========+========+
| Rent          | Company 2 |        | 180    |
+---------------+-----------+--------+--------+
| Due From      | Company 2 | 180    |        |
+---------------+-----------+--------+--------+

In the other company, a journal entry is created in the Due To/Due From
journal:

+---------------+---------------+--------+--------+
| Account       | Partner       | Debit  | Credit |
+===============+===============+========+========+
| Due To        | YourCompany   |        | 180    |
+---------------+---------------+--------+--------+
| Rent          | Company 2     | 180    |        |
+---------------+---------------+--------+--------+
