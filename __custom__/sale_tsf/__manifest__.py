# coding: utf-8
#
# COPYRIGHT
#    Copyright (C) 2018 Neobis

{
    'name': 'Sale The Service Factory',
    'summary': '''This module adds fields on the product card and calculate
    VAT prices.''',
    'version': '11.0.1.0.0',
    'category': 'sale',
    'author': 'Neobis',
    'license': '',
    'depends': [
        'account',
        'product',
        'website_sale'
    ],
    'data': [
        'views/product_views.xml'
    ],
    'installable': True,
}
