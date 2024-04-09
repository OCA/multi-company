import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-multi-company",
    description="Meta package for oca-multi-company Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-account_invoice_inter_company>=16.0dev,<16.1dev',
        'odoo-addon-account_multicompany_easy_creation>=16.0dev,<16.1dev',
        'odoo-addon-account_reconcile_model_multicompany_propagate>=16.0dev,<16.1dev',
        'odoo-addon-base_multi_company>=16.0dev,<16.1dev',
        'odoo-addon-company_dependent_flag>=16.0dev,<16.1dev',
        'odoo-addon-mail_multicompany>=16.0dev,<16.1dev',
        'odoo-addon-mail_template_multi_company>=16.0dev,<16.1dev',
        'odoo-addon-partner_multi_company>=16.0dev,<16.1dev',
        'odoo-addon-product_account_multicompany_default>=16.0dev,<16.1dev',
        'odoo-addon-product_category_company>=16.0dev,<16.1dev',
        'odoo-addon-product_category_company_favorite>=16.0dev,<16.1dev',
        'odoo-addon-product_tax_multicompany_default>=16.0dev,<16.1dev',
        'odoo-addon-purchase_sale_container_deposit_inter_company>=16.0dev,<16.1dev',
        'odoo-addon-purchase_sale_inter_company>=16.0dev,<16.1dev',
        'odoo-addon-purchase_sale_stock_inter_company>=16.0dev,<16.1dev',
        'odoo-addon-res_company_active>=16.0dev,<16.1dev',
        'odoo-addon-res_company_category>=16.0dev,<16.1dev',
        'odoo-addon-res_company_code>=16.0dev,<16.1dev',
        'odoo-addon-res_company_search_view>=16.0dev,<16.1dev',
        'odoo-addon-sale_product_company>=16.0dev,<16.1dev',
        'odoo-addon-sale_stock_warehouse_multicompany>=16.0dev,<16.1dev',
        'odoo-addon-stock_intercompany>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
