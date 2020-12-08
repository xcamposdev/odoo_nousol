# -*- coding: utf-8 -*-
{
    'name': "Credit Control Custom Field",
    'version': '1.0.0.0',
    'author': "Develoop Software",
    'category': 'Uncategorized',
    'summary': 'Credit Control, campos personalizados adicionales.',
    'website': "https://www.develoop.net/",
    'description': """
        - Credit Control, campos personalizados adicionales
        """,
    'depends': ['base','account'],
    'data': [
        'views/custom_nousol_credit_control.xml',
    ],
    'demo': [],
    "images": ['static/description/icon.png'],
    "installable": True,
    "application": True,
    "auto_install": False,
}