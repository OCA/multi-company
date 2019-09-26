import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo11-addons-oca-multi-company",
    description="Meta package for oca-multi-company Odoo addons",
    version=version,
    install_requires=[
        'odoo11-addon-account_invoice_inter_company',
        'odoo11-addon-account_multicompany_easy_creation',
        'odoo11-addon-base_multi_company',
        'odoo11-addon-ir_actions_report_multi_company',
        'odoo11-addon-partner_multi_company',
        'odoo11-addon-product_multi_company',
        'odoo11-addon-product_tax_multicompany_default',
        'odoo11-addon-purchase_sale_inter_company',
        'odoo11-addon-stock_move_line_multi_company_security',
        'odoo11-addon-stock_production_lot_multi_company',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
