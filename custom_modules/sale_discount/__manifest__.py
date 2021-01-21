# -*- coding: utf-8 -*-
{
    'name': 'sale discount custom',
    'version': '1.0.0.0',
    'author': 'Develoop Software S.A.',
    'category': 'Develoop',
    'website': 'https://www.develoop.net/',
    'depends': ['base','sale','sale_management','account'],
    'summary': 'Descuento en venta',
    'description': """
        Descuento en venta
        """,
    'data': [
        #'views/account_discount.xml',
        'views/product_discount.xml',
        'views/partner_discount.xml',
        'views/sale_discount.xml',
    ],
    'images': ['static/description/icon.png'],
    'demo': [],
    'installable': True,
}
