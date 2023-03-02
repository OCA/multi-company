import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-multi-company",
    description="Meta package for oca-multi-company Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-account_invoice_inter_company>=16.0dev,<16.1dev',
        'odoo-addon-product_tax_multicompany_default>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
