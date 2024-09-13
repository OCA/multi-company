This module adds company_id to the models ir.mail_server, mail.message and fetchmail.server. Also inherits mail.message create function to set the company mail_server
and the mail.thread message_process function to set the correct self.env.company when fetching from the incoming mail servers through a scheduled action.
