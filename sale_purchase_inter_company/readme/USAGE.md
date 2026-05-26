To allow a sale order in company A to create an associated purchase
order in company B, one must enable it in company B's settings:

1.  Choose the current company in Odoo's top menu (to the right, next no
    the user's name).
2.  Go to menu *Settings / General Settings*.
3.  Under section *Companies*, heading *Inter Company OCA features*,
    under *Sale / Purchase* check the first option, which enables this
    functionality.
4.  The selector below allows you to choose a user which will appear as
    the creator of these purchase orders. If you do not choose a user,
    the user who created the sale order will be used. In any case, the
    user needs to have permission to create purchase orders in this
    company.
5.  If you check the option of automatic validation, when you confirm
    the sale order in company A with company B as the customer, the
    purchase order will be automatically confirmed in company B.

These steps should be repeated for each company where you want to accept
the creation of such purchase orders.

**Important:** Checking in a company the option to allow the creation of
purchase orders associated with sale orders will allow this to be done
*from any other company* in Odoo (as long as the creating user has the
required permissions).
