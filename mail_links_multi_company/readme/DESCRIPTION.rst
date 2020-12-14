By default, the mail notifications with actions (such as "View Invoice", "Approve Leave" or "View Task") get base_url from the system parameter "web.base.url".
In multi-company, this is wrong since this parameter is server wide and not per company.
This module fixes that by:
1. using a company-specific url depending on the related record's company.
2. default to the system parameter "web.base.url" it the related record has no company field
