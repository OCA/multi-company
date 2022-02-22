import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-multi-company",
    description="Meta package for oca-multi-company Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-account_invoice_inter_company',
        'odoo14-addon-company_dependent_attribute',
        'odoo14-addon-mail_multicompany',
        'odoo14-addon-purchase_sale_inter_company',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
