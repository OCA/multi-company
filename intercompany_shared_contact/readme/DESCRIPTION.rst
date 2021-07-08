This module automatically shares all the contacts originating from companies (res.company object).

For example, suppose we have a multi-company environment with two companies (res.company) A and B in Odoo.
We have users uA, uB (belonging to their respective companies).

Normally, uA cannot access the contact B.
With this module, uA can see B (and inversely uB can see A).
uA still can't see all the other (supplier/reseller) contacts of company B.
