This module extends the Odoo multi-company functionality to support auto-selection of company by the domain name of the URL used to access Odoo.

This allows you to have two browsers or browser tabs open at the same time, logged in as the same user, but with two different active companies. Instead of continually switching between companies, eg. when you need to input a quotation belonging to another company, you can just switch to the second tab immediately and input the quotation there.

You can, but don't have to configure a domain name on a company. Once a regular user accesses Odoo through this domain name, his active company for that session becomes that company. Any subsequent requests through that domain name will also use that company, however, the selection is not saved in the database - so on any other domain name Odoo will still exhibit the regular behaviour of using the company that the user last switched to manually.

As a practical example, we could have:

#. company1.hosting.co: always has company 1 active
#. company2.hosting.co: always has company 2 active
#. switchable.hosting.co: has the regular Odoo behaviour of being able to switch company, and the selection being remembered until switching again

