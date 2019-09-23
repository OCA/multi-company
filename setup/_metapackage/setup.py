import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-multi-company",
    description="Meta package for oca-multi-company Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-account_invoice_inter_company',
        'odoo12-addon-base_multi_company',
        'odoo12-addon-res_company_active',
        'odoo12-addon-res_company_category',
        'odoo12-addon-stock_move_line_multi_company_security',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
