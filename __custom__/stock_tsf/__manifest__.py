# coding: utf-8
#
# COPYRIGHT
#    Copyright (C) 2018 Neobis

{
    'name': 'Stock The Service Factory',
    'summary': '''This module customizes the delivery slip, including DHL
        labels in it.''',
    'version': '11.0.1.0.0',
    'category': 'stock',
    'author': 'Neobis',
    'license': '',
    'depends': [
        'delivery_dhlp',
    ],
    'data': [
        'views/report_deliveryslip.xml',
    ],
    'installable': True,
}
