import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-multi-company",
    description="Meta package for oca-multi-company Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-account_invoice_inter_company',
        'odoo13-addon-account_multicompany_easy_creation',
        'odoo13-addon-base_multi_company',
        'odoo13-addon-company_dependent_attribute',
        'odoo13-addon-mail_multicompany',
        'odoo13-addon-mail_template_multi_company',
        'odoo13-addon-partner_multi_company',
        'odoo13-addon-product_multi_company',
        'odoo13-addon-product_tax_multicompany_default',
        'odoo13-addon-purchase_sale_inter_company',
        'odoo13-addon-purchase_sale_stock_inter_company',
        'odoo13-addon-res_company_code',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 13.0',
    ]
)
