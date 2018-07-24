import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-oca-multi-company",
    description="Meta package for oca-multi-company Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-account_invoice_inter_company',
        'odoo10-addon-account_type_multi_company',
        'odoo10-addon-base_multi_company',
        'odoo10-addon-partner_multi_company',
        'odoo10-addon-product_multi_company',
        'odoo10-addon-sale_layout_multi_company',
        'odoo10-addon-stock_production_lot_multi_company',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
