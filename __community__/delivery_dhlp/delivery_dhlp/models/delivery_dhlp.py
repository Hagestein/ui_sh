# COPYRIGHT
#    Copyright (C) 2018 Neobis

import base64
import json
import logging
import requests
from urllib import parse as urlparser

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.delivery_dhlp import utils


# TODO: consider using `keychain` for storing the user credentials
# https://github.com/OCA/server-tools/tree/10.0/keychain
# _inherit = 'keychain.account'


class DHLParcelProvider(models.Model):
    _inherit = 'delivery.carrier'

    logger = logging.getLogger('dhlp.models.dhlp')

    delivery_type = fields.Selection(selection_add=[('dhlp', 'DHL Parcel')])
    dhlp_acc_name = fields.Char(string='DHL Parcel Account Name')
    dhlp_acc_id = fields.Char(string='DHL Parcel Account ID')
    dhlp_base_url = fields.Char(
        string='DHL Parcel API Base URL',
        help=_('Example: https://api-gw.dhlparcel.nl/.\n'
               'Scheme (https) and trailing slash (/) are required.'),
    )
    dhlp_api_userid = fields.Char(string='DHL Parcel API UserID')
    dhlp_api_key = fields.Char(string='DHL Parcel API Key')
    dhlp_api_access_token = fields.Char()
    # stores Unix timestamp as an integer
    dhlp_api_access_token_exp = fields.Integer()
    dhlp_api_refresh_token = fields.Char()
    # stores Unix timestamp as an integer
    dhlp_api_refresh_token_exp = fields.Integer()

    @api.constrains('dhlp_base_url')
    def _check_validate_base_url(self):
        for record in self:
            if not record.dhlp_base_url.startswith('http'):
                raise ValidationError(_(
                    'The url must contain scheme (for example, `https://.../`)'
                ))

    @api.onchange('dhlp_base_url')
    def _onchange_dhlp_base_url(self):
        # add trailing slash if base url does not have it
        for record in self:
            if self.dhlp_base_url and not self.dhlp_base_url.endswith('/'):
                self.dhlp_base_url += '/'

    @api.multi
    def write(self, vals):
        '''Requests new tokens, if certain data
        has been changed by the user.'''
        for record in self:
            # if DHLP record exists and certain field(s) w(as|ere)
            # changed, then request a new token
            ts = record.read_group([('name', '=', 'DHL Parcel')],
                                   ['name'],
                                   ['name'])
            fields = record._set_auth_data(vals)
            if fields and ts:
                req_data = dict(
                    base_url=self.dhlp_base_url,
                    auth=dict(
                        userId=self.dhlp_api_userid,
                        key=self.dhlp_api_key,
                    ),
                )
                for k, v in fields.items():
                    if k == 'dhlp_base_url' and v:
                        req_data.update({'base_url': v})
                    elif k == 'dhlp_api_userid' and v:
                        req_data.update({'userId': v})
                    elif k == 'dhlp_api_key' and v:
                        req_data.update({'key': v})

                tokens_json = record._request_tokens(req_data)
                if not utils.validate_tokens(tokens_json):
                    raise ValidationError(_(
                        'DHL Parcel tokens are not valid. '
                        'Please try again later.\n'
                        'If the problem persists, contact support.'
                    ))

                vals.update({
                    'dhlp_api_access_token': tokens_json.get('accessToken'),
                    'dhlp_api_access_token_exp': tokens_json.get(
                        'accessTokenExpiration'),
                    'dhlp_api_refresh_token': tokens_json.get('refreshToken'),
                    'dhlp_api_refresh_token_exp': tokens_json.get(
                        'refreshTokenExpiration'),
                })

        # if carrier record does not exist, just save the existing data
        return super().write(vals)

    def dhlp_rate_shipment(self, order):
        ''' Compute the price of the order shipment
        :param order: record of sale.order
        :return dict: {'success': boolean,
                       'price': a float,
                       'error_message': a string containing
                            an error message or None,
                       'warning_message': a string containing
                            a warning message or None}
                       # TODO maybe the currency code?
        '''
        return {
            'success': True,
            'price': 0.0,
            'error_message': None,
            'warning_message': None,
        }

    def dhlp_send_shipping(self, pickings):
        ''' Send the package to the service provider
        :param pickings: A recordset of pickings
            - instances of `delivery.stock_picking` model
        :return list: A list of dictionaries (one per picking) containing
            of the form::
            { 'exact_price': price,
              'tracking_number': number }
        '''
        self.logger.info('Sending shipment orders to DHL Parcel ...')
        for rec in self:
            ship_list = []
            for pick in pickings:
                ship_list.append(rec._send_single_shipping(pick))

            return ship_list

    def dhlp_get_tracking_link(self, picking):
        ''' Ask the tracking link to the service provider
        :param picking: record of stock.picking
        :return str: a URL, containing the tracking link or False
        '''
        raise ValidationError(_(
            'The shipment Track & Trace is not implemented.'
        ))

    def dhlp_cancel_shipment(self, pickings):
        ''' Cancel a shipment
        :param pickings: A recordset of pickings
        '''
        raise ValidationError(_(
            'The shipment cancelling is not implemented.'
        ))

    def _set_auth_data(self, vals):
        data = ('dhlp_base_url', 'dhlp_api_userid', 'dhlp_api_key')
        fields = {k: v for k, v in vals.items() if k in data}
        self.logger.info('Updated fields: {0}'.format(fields))
        return fields

    def _set_headers(self, auth=True):
        '''Constructs the header of the request with the Authorization
        by default. For the tokens requests, set auth to False.'''
        self.logger.info('Setting up headers ...')
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json;charset=UTF-8',
        }
        if auth:
            if not utils.validate_tokens(self._get_tokens()):
                resp_json = self._request_tokens({
                    'base_url': self.dhlp_base_url,
                    'auth': {
                        'userId': self.dhlp_api_userid,
                        'key': self.dhlp_api_key,
                    },
                })
                self.dhlp_api_access_token = resp_json.get('accessToken')

            headers.update({
                'Authorization': 'Bearer {0}'.format(
                    self.dhlp_api_access_token)
            })

        self.logger.info('Headers have been setup.')
        return headers

    def _request_tokens(self, req_data):
        '''Requests tokens from DHL Parcel.

        :param req_data: dictionary with the request data in the form:
            {
                'base_url': <base url>,  # required
                'data': {
                    # only one of `auth` and `refreshToken` must be specified
                    'auth': {
                        'userId': <user id>,
                        'key': <api key>,
                    },
                    'refreshToken': <refresh token>,
                },
            }
        '''
        self.logger.info('Requesting new DHLP token ...')
        base_url = req_data.get('base_url')
        auth = req_data.get('auth')
        refresh = req_data.get('refreshToken')
        if auth and refresh:
            raise KeyError('Please specify only one of '
                           '`auth` and `refreshToken`')
        elif auth:
            # construct a request to DHL Parcel
            # for new refresh and access tokens
            self.logger.info('Requesting new DHLP tokens with an API key ...')
            url = urlparser.urljoin(base_url, 'authenticate/api-key')
            data = {'userId': auth.get('userId'),
                    'key': auth.get('key')}
        elif refresh:
            # construct a request to DHL Parcel for a new access token
            self.logger.info('Requesting new access token'
                             ' with a refresh token ...')
            url = urlparser.urljoin(base_url,
                                    'authenticate/refresh-token')
            data = {'refreshToken': refresh}

        # make the request
        headers = self._set_headers(auth=False)
        resp = requests.post(
            url,
            headers=headers,
            data=json.dumps(data),
            timeout=3,  # specify timeout interval in seconds
        )
        if not resp.ok:
            self.logger.error(
                'Received response from DHL Parcel API:\n'
                'status code: %s\ncontent type: %s' % (
                    resp.status_code,
                    resp.headers.get('content-type'),
                )
            )
            raise ValidationError(
                'You may have used the wrong URL '
                'or other DHL Parcel credentials. '
                'Please check your data and try again.'
                '\nIf the problem persists, please contact support.'
                '\nstatus code: {0}'.format(resp.status_code)
            )

        self.logger.info('Received new tokens.')
        resp_json = utils.validate_dhlp_response(resp)
        self._set_tokens(resp_json)
        return resp_json

    def _set_tokens(self, tokens_json):
        # FIXME This does not save tokens to the DB immediately.
        # The tokens are not saved after being received from DHLP,
        # but only when the delivery order is validated and saved.
        # This can be changed to save the tokens before the delivery
        #order is saved, so the next time there is no need to request
        # them again.

        self.dhlp_api_access_token = tokens_json.get('accessToken')
        self.dhlp_api_access_token_exp = tokens_json.get(
            'accessTokenExpiration')
        self.dhlp_api_refresh_token = tokens_json.get('refreshToken')
        self.dhlp_api_refresh_token_exp = tokens_json.get(
            'refreshTokenExpiration')

    def _get_tokens(self):
        tokens = {
            'accessToken': self.dhlp_api_access_token,
            'accessTokenExpiration': self.dhlp_api_access_token_exp,
            'refreshToken': self.dhlp_api_refresh_token,
            'refreshTokenExpiration': self.dhlp_api_refresh_token_exp,
        }
        return tokens

    def _send_single_shipping(self, picking):
        ''' Create labels for a single picking.
        :param pickings: A recordset of pickings
            - instances of `delivery.stock_picking` model
        '''
        # get order reference
        order_ref = picking.origin
        sale_order = self.env['sale.order'].search([('name', '=', order_ref)])
        # construct the URL
        url = urlparser.urljoin(self.dhlp_base_url, 'labels')
        headers = self._set_headers()
        dc = utils.DataCollector(self, order=sale_order, picking=picking)
        # instantiate pdf converter object
        pdf_conv = utils.PDFConverter(self, picking)
        # request label for every package in the picking order
        resp_json = {}
        packs = picking.number_of_packages
        if not packs:
            raise UserError(_(
                'Please specify the number of packages to be shipped.'))

        for pack_num in range(1, packs+1):
            parcel_type = 'SMALL'  # hardcoded for now
            ship_data = dc.collect_shipping_data(self.dhlp_acc_id,
                                                 parcel_type,
                                                 pack_num)
            try:
                resp = requests.post(
                    url,
                    headers=headers,
                    data=json.dumps(ship_data),
                    timeout=3,  # specify timeout interval in seconds
                )
            except requests.exceptions.RequestException as ex:
                # when timeout, returns an exception
                self.logger.error('Cannot connect to DHL Parcel server.\n', ex)
                raise ValidationError(_(
                    'Cannot get the shipping label. '
                    'Please try again later.\n'
                    'If the problem persists, contact support.'
                ))

            resp_json = utils.validate_dhlp_response(resp)
            if not resp.ok:
                err = self._parse_dhlp_error(resp_json)
                self.logger.error('Label was not created\n%s' % err)
                raise ValidationError(_(err))

            # convert pdf to image format
            pdf_conv.save_as_jpeg(
                base64.b64decode(resp_json.get('pdf')), pack_num)

        # get routing code instead of tracking code
        return {'exact_price': 0,
                'tracking_number': resp_json.get('routingCode')}

    def _parse_dhlp_error(self, resp_json):
        key = resp_json.get('key')
        msg = resp_json.get('message')
        det = resp_json.get('details')
        if key == 'capabilities_retrieve_empty':
            det = ''
            for s in [
                    'One of the possible causes of this error',
                    ' can be that either the sender or the receiver',
                    ' of the shipment has the address, which is not in the',
                    ' DHL Parcel delivery range.',
                    ' DHL Parcel only serves the limited number of countries.',
                    ' Please check the addresses of both the sender and',
                    ' the receiver and try again.',
                    '\nIf this is not the case and the error persists,',
                    ' please contact support.']:
                det += s

        return 'Error: {key}\nDescription: {msg}\nDetails: {det}'.format(
            key=key, msg=msg, det=det)
