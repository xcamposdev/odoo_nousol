# -*- coding: utf-8 -*-
{
    'name': "account_invoicing_custom",

    'summary': """
        Customizacion reports facturación""",

    'description': """
        Customizacion reports facturación
    """,

    'author': "Develoop Software",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml',
    ],
}