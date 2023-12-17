This module is usefull in a multi-company context if
- the companies doesn't have to use all the same categories
- if you apply companies to your products.

Without that module, when creating products, end user can select categories
that don't make sense for the current company.
With that module, categories manager can set for each company, which category
will be displayed, reducing configuration error. (and so accounting error
if accounts are set at the category level.)

You could be interested by concurrent module named ``product_category_company``,
(same repository), that propose similar features but with alternative implementation.

**Note**

- When creating **new root category**:

    - it is favorite for all the other company if it is favorite in the current
      context.
    - it is not favorite for all the other company if it is not favorite in the current
      context.

- When creating **new child category**:

    - the category will inherit the configuration
      of the parent category in each company.

- when creating a **new company**:

    - all the existing categories are favorite in the new created company.
