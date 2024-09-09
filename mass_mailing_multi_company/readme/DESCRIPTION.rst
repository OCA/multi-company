This module adds the company_id field to the models mailing.mailing, mailing.list, mailing.contact and mailing.contact.subscription.
It also ensures that the lists available for selection in the mailing.mailing and mailing.contact forms are restricted by the company_id value.
For the mailing.mailing domain, an expression matching only contacts/mailing contacts with the same company or without company is added when parsing the domain.

