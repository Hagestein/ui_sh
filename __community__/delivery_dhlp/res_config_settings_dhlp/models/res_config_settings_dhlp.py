# COPYRIGHT
#    Copyright (C) 2018 Neobis

from odoo import fields, models


class DHLPResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_delivery_dhlp = fields.Boolean("DHL Parcel")
