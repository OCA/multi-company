# coding: utf-8
# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Company Categories',
    'version': '8.0.1.0.0',
    'category': 'Tools',
    'author': 'GRAP',
    'website': 'http://www.grap.coop',
    'license': 'AGPL-3',
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/view_res_company.xml',
        'views/view_res_company_category.xml',
    ],
    'demo': [
        'demo/res_groups.xml',
        'demo/res_company_category.xml',
        'demo/res_company.xml',
    ],
    'installable': True,
    'images': [
        'static/description/res_company_category_form.png',
        'static/description/res_company_category_tree.png',
        'static/description/res_company_form.png',
    ],
}
