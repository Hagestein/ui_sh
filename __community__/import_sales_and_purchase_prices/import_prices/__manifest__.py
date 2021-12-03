# coding: utf-8
#
# COPYRIGHT
#    Copyright (C) 2018 Neobis

{
    'name': 'Import Sales And Purchase Prices',
    'summary': '''This module introduces a wizard to import the sales and cost
        prices of products from xlsx file and update the vendors price lists
        with the imported prices.''',
    'version': '11.0.1.0.0',
    'category': 'purchase/sale',
    'author': 'Neobis',
    'license': '',
    'depends': [
        'product',
        'purchase',
    ],
    'external_dependencies': {
        'python': [
            'pyexcel',
        ],
    },
    'data': [
        'wizard/import_prices_importer_views.xml',
        'views/product_supplierinfo_views.xml',
    ],
    'installable': True,
}
