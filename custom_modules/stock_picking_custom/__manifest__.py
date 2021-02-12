# -*- coding: utf-8 -*-
{
    'name': "Stock Picking Custom",
    'version': "1.0.0",
    'author': "Develoop Software",
    'category': "Stock",
    'summary': "Modificaciones en Inventario",
    'website': "https://www.develoop.net/",
    'description': """
        - Modificacion del campo Referencia de segimiento
    """,
    'depends': ['stock','delivery'],
    'data': [
        'views/stock_picking_custom.xml',
    ],
    'images': ['static/description/icon.png'],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
