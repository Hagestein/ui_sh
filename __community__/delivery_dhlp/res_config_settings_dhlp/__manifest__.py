# COPYRIGHT
#    Copyright (C) 2018 Neobis

{
    'name': 'Configuration Settings DHL Parcel',
    'summary': '''This module creates a configuration settings
        functionality for DHL Parcel.''',
    'version': '11.0.1.0.0',
    'author': 'Neobis',
    'license': '',
    'depends': [
        'delivery',
        'sale',
        'stock',
    ],
    'data': [
        'views/res_config_settings_views_dhlp.xml',
    ],
    'installable': True,
    'autoinstall': True,
}
