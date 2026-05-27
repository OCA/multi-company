In models like project.task that interact directly with customers, incoming emails add 
CC addresses as followers, but the company restriction is not considered. In a multi-company
environment, if a customer sends an email with a CC address that belongs to a contact
dedicated to another company, that contact is added as a follower. Since the user lacks
access rights to that contact’s company, they get an access error viewing the record.

This module addresses the issue by adding a company domain when matching email addresses
to contacts.
