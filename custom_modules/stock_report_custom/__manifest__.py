# -*- coding: utf-8 -*-
{
    'name': "sale_report_custom",

    'summary': """
        Customizacion reports inventario""",

    'description': """
        Customizacion reports inventario
    """,

    'author': "Develoop Software",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml',
    ],
}