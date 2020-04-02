import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-multi-company",
    description="Meta package for oca-multi-company Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-account_invoice_inter_company',
        'odoo13-addon-company_dependent_attribute',
        'odoo13-addon-purchase_sale_inter_company',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
