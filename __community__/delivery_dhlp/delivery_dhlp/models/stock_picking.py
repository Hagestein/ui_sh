# COPYRIGHT
#    Copyright (C) 2018 Neobis

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    dhlp_label_ids = fields.One2many(
        'ir.attachment',
        'dhlp_stock_picking_id',
        ondelete='restrict',
        string='Labels',
    )
