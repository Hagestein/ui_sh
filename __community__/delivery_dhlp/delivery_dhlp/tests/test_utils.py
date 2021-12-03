#!/bin/env python3

# run tests with --test-enable and --stop-after-init flags

# flake8: noqa

from datetime import datetime, timedelta, timezone
from unittest import mock
from urllib import parse as urlparser

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

from odoo.addons.delivery_dhlp.models.delivery_dhlp import (
    DHLParcelProvider as DHLP,
)
from odoo.addons.delivery_dhlp.utils import DataCollector


class UtilsTests(TransactionCase):

    def setUp(self):
        super().setUp()
        self.so1 = self.env.ref('sale.sale_order_1')
        self.carrier = DHLP()
        self.dc = DataCollector(self.carrier, order=self.so1)

    # TODO
#    def test_collect_shipping_data(self):
#        order = self._create_sale_order()
#        order.action_draft()
#        order.action_confirm()
#        dc = DataCollector(self.carrier, order=order, pickings=pickings)

    # TODO
    def test_get_receiver_data_location(self):
        # partner: base.res_partner_2
        partner = self.dc._get_receiver_data_location()
        # assert location is the partner, if partner has no parent
        self.assertEqual(partner, self.dc.order.partner_id)
        # assert location is the parent of the partner, if partner has a parent
        # set a new partner with a parent on the sale order
        partner = self.env.ref('base.res_partner_address_1')
        self.dc.order.partner_id = partner
        # parent: base.res_partner_1
        parent = self.dc._get_receiver_data_location()
        self.assertEqual(parent, partner.parent_id)

    # TODO
    def test_get_participant_name(self):
        # assert for receiver
        partner = self.dc.order.partner_id
        receiver = partner or partner.parent_id
        test_dict = {'lastName': receiver.display_name,
                     'companyName': receiver.display_name}
        name_dict = self.dc._get_participant_name('receiver')
        self.assertDictEqual(test_dict, name_dict)
        # assert for shipper
        test_dict = {'companyName': self.so1.company_id.name}
        name_dict = self.dc._get_participant_name('shipper')
        self.assertDictEqual(test_dict, name_dict)
        # assert error is raised if wrong type is supplied
        self.assertRaises(UserError,
                          self.dc._get_participant_name,
                          part_type='bla-bla')

    def test_get_address(self):
        # assert for receiver
        partner = self.so1.partner_id
        receiver = partner or partner.parent_id
        test_addr = {
            'countryCode': receiver.country_id.code.upper(),
            'postalCode': receiver.zip.upper(),
            'city': receiver.city,
            'street': receiver.street,
        }
        addr = self.dc._get_address('receiver')
        self.assertDictEqual(test_addr, addr)
        # assert for shipper
        shipper = self.so1.company_id
        test_addr = {
            'countryCode': shipper.country_id.code.upper(),
            'postalCode': shipper.zip.upper(),
            'city': shipper.city,
            'street': shipper.street,
        }
        addr = self.dc._get_address('shipper')
        self.assertDictEqual(test_addr, addr)
        # assert error is raised if wrong argument is supplied
        self.assertRaises(ValueError,
                          self.dc._get_address,
                          part_type='bla-bla')
        # assert error is raised
        # if code is not setup correctly for the receiver
        receiver.country_id.code = ''
        self.assertRaises(UserError,
                          self.dc._get_address,
                          part_type='receiver')
        # assert error is raised
        # if code is not setup correctly for the shipper
        self.so1.company_id.country_id.code = 'r'
        self.assertRaises(UserError,
                          self.dc._get_address,
                          part_type='shipper')

    # TODO
    def test_get_participant_address(self):
        pass

    # TODO
    def test_get_participant_other_data(self):
        pass

    # TODO
    def test_validate_required_fields(self):
        pass

    # TODO
    def test_collect_participant_data(self):
        pass
