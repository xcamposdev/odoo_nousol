# -*- coding: utf-8 -*-
{
    'name': "purchase_report_custom",

    'summary': """
        Customizacion reports compras""",

    'description': """
        Customizacion reports compras
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['purchase','product_pack'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml',
    ],
}