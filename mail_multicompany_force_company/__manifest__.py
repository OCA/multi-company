{
    "name": "Email Multi Company Force Company Server",
    "category": "Extra Tools",
    "description": """
       Email Multi Company Force Company Server:
        This module forces to use the mail server that is configured for the company in outgoing mail server configuration.\n
        If there is a mail server without a company assigned, it will be used by all companies.\n
        In case there is a mail server without company and your company has assigned a mail server, you will use your company's mail server
    """,
    "version": "15.0.1.0.0",
    "author": "Infraestructuras Tecnológicas de Cantabria, S.L.",
    "website": "https://github.com/OCA/multi-company",
    "license": "AGPL-3",
    "depends": ["mail_multicompany", "base"],
    "data": ["views/ir_mail_server_views.xml"],
    "application": False,
    "installable": True,
    "auto_install": False,
}
