# -*- coding: utf-8 -*-
#
# COPYRIGHT
#    Copyright (C) 2018 Neobis

import base64
import os

from odoo.tests.common import TransactionCase


class TestImport(TransactionCase):

    def setUp(self):
        super().setUp()
        self.wizard = self.env['import.prices.importer'].create({})
        self.product_id = self.env['product.template']
        supplier_id = self.env['res.partner'].create({
            'name': 'Supplier'})
        self.product_1 = self.product_id.create({
            'name': 'Product A',
            'default_code': 'TEST1'})
        self.product_2 = self.product_id.create({
            'name': 'Product B',
            'default_code': 'TEST2',
            'seller_ids': [(0, None, {
                'name': supplier_id.id,
                'price': 200})]
        })

    def test_import_xlsx(self):
        '''Test import for a xlsx file'''
        filename = os.path.join(
            os.path.dirname(__file__),
            'test_files' + os.path.sep + 'test_1.xlsx')
        with open(filename, mode='rb') as f:
            self.wizard.prices_file = base64.b64encode(f.read())
        self.wizard.filename = 'test_1.xlsx'
        self.wizard.action_import()
        self.product_1.refresh()
        self.product_2.refresh()
        self.assertEqual(self.product_1.standard_price, 200)
        self.assertEqual(self.product_2.standard_price, 300)
        self.assertEqual(self.product_2.list_price, 350)
        self.assertEqual(self.product_2.seller_ids.price, 300)

    def test_import_xls(self):
        '''Test import for a xls file'''
        filename = os.path.join(
            os.path.dirname(__file__),
            'test_files' + os.path.sep + 'test_1.xls')
        with open(filename, mode='rb') as f:
            self.wizard.prices_file = base64.b64encode(f.read())
        self.wizard.filename = 'test_1.xlsx'
        self.wizard.action_import()
        self.product_1.refresh()
        self.product_2.refresh()
        self.assertEqual(self.product_1.standard_price, 200)
        self.assertEqual(self.product_2.standard_price, 300)
        self.assertEqual(self.product_2.list_price, 350)
        # seller_ids is a One2many, but since we know that we have one
        # seller in this test we can get away with using seller_ids.price.
        self.assertEqual(self.product_2.seller_ids.price, 300)
