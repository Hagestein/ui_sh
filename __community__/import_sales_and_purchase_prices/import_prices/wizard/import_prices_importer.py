# -*- coding: utf-8 -*-
#
# COPYRIGHT
#    Copyright (C) 2018 Neobis

import base64
import os.path

import pyexcel

from odoo import fields, models


class ImportPricesImporter(models.TransientModel):
    _name = 'import.prices.importer'

    prices_file = fields.Binary()
    filename = fields.Char('filename')

    def action_import(self):
        '''Import a spreadsheet and set the prices on products that match the
        'default_code' field.

        The spreadsheet is expected to match the following layout:
        ------------------------------------------
        - default code - cost price - sale price -
        ------------------------------------------
        - CODE         - 400        - 500        -
        ------------------------------------------
        - CODE2        - 400        - 500        -
        ------------------------------------------

        Where the text in the first row does not matter for this function.

        Currently the following formats are supported:
         - .xlsx
         - .xls
        '''
        # 'splitext' returns path + extension in tuple
        # Cleanup the extension so we will always get something like 'xls'
        file_type = os.path.splitext(self.filename)[1][1:].strip().lower()
        file_dec = base64.b64decode(self.prices_file)
        spreadsheet = pyexcel.get_sheet(
            file_content=file_dec,
            file_type=file_type,
            start_row=1,
            column_limit=3)
        for row in spreadsheet:
            # Find the product by product code
            product_id = self.env['product.template'].search(
                [('default_code', '=', row[0])],
                limit=1)
            if product_id:
                product_id.standard_price = row[1]
                product_id.list_price = row[2]
                if product_id.seller_ids:
                    product_id.seller_ids.price = row[1]
        return True
