# coding: utf-8
#
# COPYRIGHT
#    Copyright (C) 2018 Neobis

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    website_title = fields.Char("Website Title")
    website_specifications = fields.Html('Website Specifications')
    image_2 = fields.Binary(
        "Image 2", attachment=True)
    image_2_title = fields.Char("Image 2 Title")
    image_3 = fields.Binary(
        "Image 3", attachment=True)
    image_3_title = fields.Char("Image 3 Title")
    image_4 = fields.Binary(
        "Image 4", attachment=True)
    image_4_title = fields.Char("Image 4 Title")
    image_5 = fields.Binary(
        "Image 5", attachment=True)
    image_5_title = fields.Char("Image 5 Title")
    price_incl_vat = fields.Float("Price incl. VAT",
                                  compute="_compute_vat_price")

    def _compute_vat_price(self):
        for product in self:
            product.price_incl_vat = product.list_price * \
                                     (1 + product.taxes_id[0].amount/100)
