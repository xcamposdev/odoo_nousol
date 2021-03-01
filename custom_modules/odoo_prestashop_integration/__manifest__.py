{
    'name': 'Prestashop Odoo Integration',
    'category': 'Sales',
    'version': '13.0',
    'summary': """Perform various operations like Import products, categories, customers , orders & and much more.""",
    'description': """""",

    'depends': ['sale_management','sale_stock','product','base'],

    'data': [
        'security/ir.model.access.csv',
        'views/prestashop_store_details.xml',
        'views/prestashop_operation_details.xml',
        'views/product_category.xml',
        'views/product.xml',
        'views/product_attribute.xml',
        'views/sale_order.xml',
        'data/ir_cron.xml',
        
    ],
    'author': 'Vraja Technologies',
    'images': ['static/description/prestashop.png'],
    'maintainer': 'Vraja Technologies',
    'website': 'www.vrajatechnologies.com',
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': '149',
    'currency': 'EUR',
    'license': 'OPL-1',

}
