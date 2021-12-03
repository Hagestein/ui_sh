# COPYRIGHT
#    Copyright (C) 2018 Neobis

{
    'name': 'DHL Parcel Connector',
    'summary': 'This module integrates the DHL Parcel API into Odoo.',
    'version': '11.0.1.0.0',
    'category': 'delivery',
    'author': 'Neobis',
    'license': '',
    'depends': [
        'delivery',
        'res_config_settings_dhlp',
        'sale',
        'stock',
    ],
    'data': [
        'data/delivery_dhlp_data.xml',
        'views/delivery_dhlp_views.xml',
    ],
    'installable': True,
}
