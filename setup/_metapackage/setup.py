import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-multi-company",
    description="Meta package for oca-multi-company Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-account_invoice_inter_company>=15.0dev,<15.1dev',
        'odoo-addon-account_multicompany_easy_creation>=15.0dev,<15.1dev',
        'odoo-addon-base_multi_company>=15.0dev,<15.1dev',
        'odoo-addon-partner_multi_company>=15.0dev,<15.1dev',
        'odoo-addon-product_multi_company>=15.0dev,<15.1dev',
        'odoo-addon-product_tax_multicompany_default>=15.0dev,<15.1dev',
        'odoo-addon-purchase_sale_inter_company>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
