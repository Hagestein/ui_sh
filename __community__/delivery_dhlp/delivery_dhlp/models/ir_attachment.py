# COPYRIGHT
#    Copyright (C) 2018 Neobis

from odoo import fields, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    dhlp_stock_picking_id = fields.Many2one('stock.picking',
                                            ondelete='cascade')
