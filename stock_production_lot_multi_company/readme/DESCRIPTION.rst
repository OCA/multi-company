This module was written to extend the functionality of serial numbers and make
them multi company aware.

This is especially important if you are using serial numbers as otherwise Odoo
may end up trying to merge stock.quant records having the same lot, but going
to the Customers location from 2 different companies (in case it was first
shipped from Company 1 to Company2) and this will fail due to a constraint.
