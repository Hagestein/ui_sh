# COPYRIGHT
#    Copyright (C) 2018 Neobis

import base64
import json
import logging
import os
import pdf2image
import uuid
from datetime import datetime, timezone

from odoo import _

from odoo.exceptions import UserError, ValidationError


logger = logging.getLogger('utils')


def validate_tokens(tokens_dict):
    '''Validates the tokens.

    :param tokens_dict: is a dictionary with access and refresh tokens in
        the form
        {
            'accessToken': <access token>,
            'accessTokenExpiration': <access token exp time as an int>,
            'refreshToken': <refresh token>,
            'refreshTokenExpiration': <refresh token exp time as an int>,
        }
    :returns: True if tokens are correct, False otherwise
    '''
    logger.info('Validating tokens ...')
    # remove microseconds
    curr_time = datetime.now(timezone.utc).replace(microsecond=0)
    # convert unix timestamp to integer
    curr_timestamp = int(curr_time.timestamp())
    a_token = tokens_dict.get('accessToken')
    a_token_exp = tokens_dict.get('accessTokenExpiration')
    r_token = tokens_dict.get('refreshToken')
    r_token_exp = tokens_dict.get('refreshTokenExpiration')
    valid = True
    if not all((a_token,
                isinstance(a_token, str),
                isinstance(a_token_exp, int),
                a_token_exp > curr_timestamp)):
        # if access token is not valid,
        # request a new one with the refresh token
        logger.error('Access token is not valid.')
        valid = False
    elif not all((r_token,
                  isinstance(r_token, str),
                  isinstance(r_token_exp, int),
                  r_token_exp > curr_timestamp)):
        # if refresh token is not valid,
        # request a new one with the API credentials
        logger.error('Refresh token is not valid.')
        valid = False
    else:
        logger.info('Tokens are valid.')

    logger.info('Tokens validation: %s' % valid)
    return valid


def validate_dhlp_response(resp):
    try:
        return resp.json()
    except json.decoder.JSONDecodeError as ex:
        logger.error('The body of the response is not formatted as JSON.\n'
                     'Response has returned the following body:\n'
                     '%s\nstatus code: %s\ncontent type: %s' % (
                         resp.text, resp.status_code,
                         resp.headers.get('content-type')))
        raise ValidationError(
            'Response from the DHL Parcel API is not known.\n'
            '{0}\nPlease contact support.'.format(ex))
    except Exception as ex:
        logger.error('Response has returned the following body:\n'
                     '%s\n and the error:\n%s' % (resp.json(), ex))
        raise ValidationError(
            'There was something wrong with the request to DHL Parcel API.'
            '\nIf the problem persists, please contact support.'
            '\n{0}'
            '\nstatus code: {1}'.format(ex, resp.status_code)
        )


class PDFConverter:
    ''' Converts PDF to image and saves it in the db.'''

    logger = logging.getLogger('utils.pdf-converter')

    def __init__(self, carrier, picking):
        self.carrier = carrier
        self.picking = picking

        # TODO
        # temporary dir can also be done with the Python `tempfile` module
        # https://docs.python.org/3.5/library/tempfile.html
        labels_dir = '/tmp/labels'
        if not os.path.exists(labels_dir):
            os.makedirs(labels_dir)

        self.labels_dir = os.path.abspath(labels_dir)
        self._clear_labels_dir()

    def save_as_jpeg(self, pdfstr, pack_num):
        ''' Save images into the db as attachments to the stock.picking.'''
        self._pdf2jpeg(pdfstr)
        # get file from the dir
        imgfiles = []
        for d, ds, files in os.walk(self.labels_dir):
            for f in files:
                imgfiles.append(
                    os.path.abspath(os.path.join(self.labels_dir, f)))

            break

        b64img = ''
        try:
            with open(imgfiles[0], 'rb') as imgfile:
                b64img = base64.b64encode(imgfile.read())
        except (IndexError, TypeError):
            err = 'No label file found.'
            self.logger.error(err)
            raise ValidationError(_('{0} Contact support.'.format(err)))

        # save the label to the picking order attachment
        # jpeg image must be stored as an attachment object
        # to the stock.picking
        fname = '{do}-label-{num}'.format(
            do=self.picking.name, num=pack_num)
        self.carrier.env['ir.attachment'].create({
            'name': fname,
            'datas_fname': fname,
            'type': 'binary',
            'db_datas': b64img,
            'dhlp_stock_picking_id': self.picking.id,
            'mimetype': 'image/jpeg',
        })
        self.logger.info('Label has been saved to the database.')
        # clear the labels dir
        self._clear_labels_dir()

    # clear the labels dir
    def _clear_labels_dir(self):
        imgfiles = os.listdir(self.labels_dir)
        [os.remove(os.path.abspath(os.path.join(self.labels_dir, f)))
         for f in imgfiles]
        self.logger.info('Temporary directory cleaned.')

    def _pdf2jpeg(self, pdfstr):
        pdf2image.convert_from_bytes(
            pdfstr, output_folder=self.labels_dir, fmt='jpeg')[0]
        self.logger.info(
            'Label has been converted and saved to a temporary location.')


class DataCollector:
    ''' Collects data for picking
    for creating a request to DHL Parcel.'''

    logger = logging.getLogger('utils.data-collector')

    def __init__(self, carrier, order=None, picking=None):
        self.logger.info('Collecting data ...')
        self.carrier = carrier
        self.order = order
        self.picking = picking

    def collect_shipping_data(self, accountid, parcel_type, pack_num):
        '''Collects data for either shipping rate request or for
        shipping request. In the case of shipping rate, the resource
        of data is `order`, in the case of shipping the source is a
        `picking`.
        '''
        data = {
            'labelId': str(uuid.uuid4()),
            'labelFormat': 'pdf',
            'orderReference': self.order.name,
            'parcelTypeKey': parcel_type,
            'receiver': self._collect_participant_data('receiver'),
            'onBehalfOf': self._get_on_behalf_of(),
            'shipper': self._collect_participant_data('shipper'),
            'accountId': accountid,
            'options': self._get_options(),
            'returnLabel': False,
            'pieceNumber': pack_num,
            'quantity': self._get_quantity(),
            'automaticPrintDialog': False,
        }
        return data

    def _collect_participant_data(self, part_type):
        part = {
            'name': self._get_participant_name(part_type),
            'address': self._get_participant_address(part_type),
        }
        part.update(self._get_participant_other_data(part_type))
        return part

    # TODO
    def _validate_required_fields(self, *fields):
        pass

    def _get_receiver_data_location(self):
        '''Get one of the partner or the parent records of the current order.
        '''
        partner_id = self.order.partner_id
        loc = partner_id.parent_id or partner_id
        for child in loc.child_ids:
            if child.type == 'delivery':
                return child

        return loc

    def _get_participant_name(self, part_type):
        '''Gets the name of the participant.'''
        if part_type == 'receiver':
            name = self._get_receiver_data_location().display_name
            return {
                'lastName': name,
                'companyName': name,
            }
        elif part_type == 'shipper':
            return {
                'companyName': self.order.company_id.name,
            }

        err = 'Cannot get the receiver/shipper name.'
        self.logger.error(err)
        raise UserError(_(err))

    def _get_address(self, part_type):
        if part_type == 'receiver':
            country_code = self._get_receiver_data_location().country_id.code
            zip_code = self._get_receiver_data_location().zip
            city = self._get_receiver_data_location().city
            street = self._get_receiver_data_location().street
        elif part_type == 'shipper':
            country_code = self.order.company_id.country_id.code
            zip_code = self.order.company_id.zip
            city = self.order.company_id.city
            street = self.order.company_id.street
        else:
            err = 'Wrong argument `part_type` specified'
            self.logger.error(err)
            raise ValueError(_(err))

        if (
                not country_code or
                not len(country_code) == 2 or
                not zip_code or
                not city or
                not street):
            self.logger.error('One of the addresses is missing data.')
            raise UserError(_('One of the following is required:\n'
                              'country code\n'
                              'postal code\n'
                              'city\n'
                              'street\n.'
                              'Please check both, the addresses of your'
                              ' company and the recipient address.'))

        return {'countryCode': country_code.upper(),
                'postalCode': zip_code.upper(),
                'city': city,
                'street': street}

    def _get_receiver_zip(self):
        return self._get_receiver_data_location().zip.upper()

    def _get_participant_address(self, part_type):
        '''Gets the address of the participant.'''
        if part_type == 'receiver':
            addr = {
                'isBusiness': self._get_receiver_data_location().is_company
                or False,
            }
        elif part_type == 'shipper':
            addr = {
                'isBusiness': self.order.company_id.partner_id.is_company
                or False,
            }

        # update with the address of the participant
        addr.update(self._get_address(part_type))
        if addr:
            return addr

        err = 'Cannot get the receiver/shipper address details.'
        self.logger.error(err)
        raise UserError(_(err))

    def _get_participant_other_data(self, part_type):
        if part_type == 'receiver':
            return {
                'email': self._get_receiver_data_location().email,
                'phoneNumber': self._get_receiver_data_location().phone,
            }
        elif part_type == 'shipper':
            return {
                'email': self.order.company_id.email,
                'phoneNumber': self.order.company_id.phone,
                'vatNumber': self.order.company_id.vat or '',
            }

        err = 'Cannot get the receiver/shipper data.'
        self.logger.error(err)
        raise UserError(_(err))

    # TODO
    def _get_on_behalf_of(self):
        '''Optional feature, only available for Benelux region. Allows to
        send package on behalf of someone else without desclosing the sender
        data in the Track&Trace info. Also requires an `option` {'key': 'SSN'}.
        '''
        return

    def _get_options(self):
        '''Optional field, which may have some extra info about the shipping.
        Check the docs.
        '''
        return [
            {
                'key': 'DOOR',
            },
            {
                'key': 'REFERENCE',
                'input': self.order.name,  # max 15 chars
            },
            {
                'key': 'REFERENCE2',
                'input': self.picking.name,  # max 70 chars
            },
        ]

    def _get_quantity(self):
        '''Get the total number of packages in the shipping order.'''
        return self.picking.number_of_packages

    # TODO
    def _get_shipping_weight(self):
        '''Specify the sequence number of the current package within the
        shipping order.'''
        return self.picking.shipping_weight
