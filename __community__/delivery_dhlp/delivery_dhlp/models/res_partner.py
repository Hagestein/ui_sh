# COPYRIGHT
#    Copyright (C) 2018 Neobis

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def default_get(self, default_fields):
        res = super().default_get(default_fields)
        carrier = self.env.ref(
            'delivery_dhlp.delivery_carrier_dhlp',
            raise_if_not_found=False)
        res.update({
            'property_delivery_carrier_id': carrier and carrier.id or False,
        })
        return res

    # readonly modifier does not allow to set default value
    property_delivery_carrier_id = fields.Many2one()
