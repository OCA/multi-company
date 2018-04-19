import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo8-addons-oca-multi-company",
    description="Meta package for oca-multi-company Odoo addons",
    version=version,
    install_requires=[
        'odoo8-addon-account_invoice_inter_company',
        'odoo8-addon-account_type_multi_company',
        'odoo8-addon-base_ir_filters_company',
        'odoo8-addon-partner_multi_company',
        'odoo8-addon-product_multi_company',
        'odoo8-addon-purchase_sale_inter_company',
        'odoo8-addon-sale_layout_multi_company',
        'odoo8-addon-stock_production_lot_multi_company',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
