# COPYRIGHT
#    Copyright (C) 2018 Neobis

# run tests with --test-enable and --stop-after-init flags

from datetime import datetime, timedelta, timezone
from unittest import mock

from odoo.tests.common import TransactionCase


class DeliveryDHLParcelTests(TransactionCase):

    def setUp(self):
        super().setUp()
        exp_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        self.at_time = int(exp_time.timestamp())
        self.carrier_data = {}
        self.carrier = self._create_carrier()
        # mock requests
        # https://stackoverflow.com/a/31595270
        patcher = mock.patch(
            'odoo.addons.delivery_dhlp.models.delivery_dhlp.requests')
        self.mock_response = mock.Mock(status_code=200)
        self.mock_response.raise_for_status.return_value = None
        self.mock_response.json.return_value = {
            'accessToken': 'new-access-token',
            'accessTokenExpiration': self.at_time,
            'refreshToken': 'new-refresh-token',
            'refreshTokenExpiration': self.at_time,
        }
        self.mock_request = patcher.start()
        self.mock_request.return_value = self.mock_response

    def tearDown(self):
        self.mock_request.stop()

    def _create_carrier(self):
        product_id = self.env['product.product'].search([], limit=1).id
        self.carrier_data = {
            'name': 'New DHL Parcel carrier',
            'product_id': product_id,  # required field
            'delivery_type': 'dhlp',  # required field
            'dhlp_base_url': 'https://url/to/api/',
            'dhlp_acc_id': 'acc-id',
            'dhlp_api_userid': 'some-id',
            'dhlp_api_key': 'some-key',
            'dhlp_api_access_token': 'access-token',
            'dhlp_api_access_token_exp': self.at_time,
            'dhlp_api_refresh_token': 'refresh-token',
            'dhlp_api_refresh_token_exp': self.at_time,
        }
        carrier = self.env['delivery.carrier'].create(self.carrier_data)
        return carrier

    def test_create_new_carrier(self):
        carrier = self._create_carrier()
        # assert record exists
        self.assertTrue(carrier.exists())
        # assert record has the correct data
        self.assertEqual(self.carrier_data.get('name'), carrier.name)
        self.assertEqual(self.carrier_data.get('dhlp_base_url'),
                         carrier.dhlp_base_url)
        self.assertEqual(self.carrier_data.get('dhlp_api_userid'),
                         carrier.dhlp_api_userid)
        self.assertEqual(self.carrier_data.get('dhlp_api_key'),
                         carrier.dhlp_api_key)

    def test_set_headers(self):
        testdata = {
            'Accept': 'application/json',
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': 'Bearer access-token',
        }
        self.assertDictEqual(testdata, self.carrier._set_headers())
        testdata = {
            'Accept': 'application/json',
            'Content-Type': 'application/json;charset=UTF-8',
        }
        self.assertDictEqual(testdata, self.carrier._set_headers(auth=False))

#    def test_request_token(self):
#        # test correct urls
#        self.assertEqual(
#            'https://url/to/api/authenticate/api-key',
#            urlparser.urljoin(self.carrier.dhlp_base_url,
#                              'authenticate/api-key')
#        )
#        self.assertEqual(
#            'https://url/to/api/authenticate/refresh-token',
#            urlparser.urljoin(self.carrier.dhlp_base_url,
#                              'authenticate/refresh-token')
#        )
#        # create a unix timestamp in python 3
#        # https://stackoverflow.com/a/15910301
#        exp_time = datetime.now(timezone.utc) + timedelta(minutes=5)
#        at_time = int(exp_time.timestamp())
#        testdata = {
#            'dhlp_api_access_token': 'new-access-token',
#            'dhlp_api_access_token_exp': at_time,
#            'dhlp_api_refresh_token': 'new-refresh-token',
#            'dhlp_api_refresh_token_exp': at_time,
#        }
#        return_data = {
#            'accessToken': 'new-access-token',
#            'accessTokenExpiration': at_time,
#            'refreshToken': 'new-refresh-token',
#            'refreshTokenExpiration': at_time,
#        }
#        self.mock_request.post.return_value = self.mock_response
#        self.mock_response.json.return_value = return_data
#        # test the function
#        self.assertDictEqual(
#            testdata,
#            self.carrier._request_token(refresh=True),
#        )

#    def test_validate_token(self):
#        # test valid token
#        self.assertFalse(self.carrier._validate_token())
#        # test invalid token - a new token must be requested
#        setattr(self.carrier, 'dhlp_api_access_token_exp', 1)
#        mock_fun = self.carrier._request_token = mock.MagicMock()
#        self.carrier._validate_token()
#        mock_fun.assert_called_with()

    # TODO
    def test_write(self):
        pass

#    def test_generate_track_url(self):
#        trackcode = 'SomeCode123'
#        zipcode = '1234AB'
#        testdata = '{0}track-trace?key={1}+{2}'.format(
#            self.carrier.dhlp_base_url,
#            trackcode,
#            zipcode,
#        )
#        trackurl = self.carrier._generate_track_url(trackcode, zipcode)
#        self.assertEqual(testdata, trackurl)

    def test_send_single_shipping(self):
        return_data = {}
        self.mock_request.post.return_value = self.mock_response
        self.mock_response.json.return_value = return_data
        pass
