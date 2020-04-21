import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-multi-company",
    description="Meta package for oca-multi-company Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-account_bill_line_distribution',
        'odoo12-addon-account_invoice_consolidated',
        'odoo12-addon-account_invoice_inter_company',
        'odoo12-addon-account_move_multi_company',
        'odoo12-addon-account_multicompany_easy_creation',
        'odoo12-addon-account_payment_other_company',
        'odoo12-addon-base_multi_company',
        'odoo12-addon-calendar_event_type_multi_company',
        'odoo12-addon-company_dependent_attribute',
        'odoo12-addon-crm_lead_tag_multi_company',
        'odoo12-addon-crm_lost_reason_multi_company',
        'odoo12-addon-crm_stage_multi_company',
        'odoo12-addon-mail_template_multi_company',
        'odoo12-addon-partner_multi_company',
        'odoo12-addon-product_multi_company',
        'odoo12-addon-product_tax_multicompany_default',
        'odoo12-addon-purchase_sale_inter_company',
        'odoo12-addon-res_company_active',
        'odoo12-addon-res_company_category',
        'odoo12-addon-res_company_code',
        'odoo12-addon-res_partner_category_multi_company',
        'odoo12-addon-stock_move_line_multi_company_security',
        'odoo12-addon-stock_production_lot_multi_company',
        'odoo12-addon-utm_medium_multi_company',
        'odoo12-addon-utm_source_multi_company',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
