# -*- coding: utf-8 -*-
{
    'name': "Product Pack Custom Cost",
    'version': '1.0.0.0',
    'author': "Develoop Software",
    'category': 'Uncategorized',
    'summary': 'Product pack, calculo de costos adicionales.',
    'website': "https://www.develoop.net/",
    'description': """
        - Product pack, calculo de costos adicionales
        """,
    'depends': ['base','sale'],
    'data': [
        'views/custom_nousol_product_pack.xml',
    ],
    'demo': [],
    "images": ['static/description/icon.png'],
    "installable": True,
    "application": True,
    "auto_install": False,
}