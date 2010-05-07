# Copyright (c) 2010 ifPeople, Kapil Thangavelu, and Contributors
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

"""

notes on error handling, if we haven't talked to the processor then raise an exception,
else return an error message so higher levels can interpret/record/notify user/etc.

$Id: $
"""

from time import strftime, gmtime

from zope import interface
from zope.annotation.interfaces import IAnnotations

from zc.authorizedotnet.processing import CcProcessor
from getpaid.authorizedotnet.subscription import ARBProcessor
from getpaid.core import interfaces

from getpaid.authorizedotnet.interfaces import IAuthorizeNetOptions

from datetime import date

SUCCESS = 'approved'

# needed for refunds
LAST_FOUR = "getpaid.authorizedotnet.cc_last_four"

APPROVAL_KEY = "getpaid.authorizedotnet.approval_code"

class AuthorizeNetAdapter(object):
    interface.implements( interfaces.IPaymentProcessor )

    options_interface = IAuthorizeNetOptions

    _sites = dict(
        Production = "secure.authorize.net:443",
        Test = "test.authorize.net:443"
        )
    _arb_sites = dict(
        Production = "api.authorize.net:443",
        Test = "apitest.authorize.net:443"
        )

    def __init__(self, context):
        self.context = context
    
    def is_recurring_order(self, order):
        recurring = 0
        non_recurring = 0
        for i in order.shopping_cart.values():
            if interfaces.IRecurringLineItem.providedBy(i):
                recurring += 1
            else:
                non_recurring += 1
        
        if recurring > 0 and non_recurring > 0:
            raise Exception('Carts containing both recurring and non-recurring items '
                            'are not supported.')
        elif recurring > 1:
            raise Exception('Carts containing multiple recurring items not supported.')
        elif recurring == 1:
            return True
        return False

    def authorize(self, order, payment):
        billing = order.billing_address
        amount = order.getTotalPrice()
        contact = order.contact_information
        order_id = order.getOrderId()
        contact_fields = 'Contact Name: ' + contact.name + \
                         ';  Contact Phone: ' + contact.phone_number  + \
                         ';  Contact Email: ' + contact.email

        expiration_date = ''
        if hasattr(payment.cc_expiration, 'strftime'):
            expiration_date = payment.cc_expiration.strftime('%m%y')
        else:
            # If cc_expiration is not of type date, then it should be 
            # a string like this: '2011-08-03 00:00'
            # This is a bug in getpaid.formgen's single page checkout
            # and the correct fix is to swap out it's expiration date
            # widget with one that returns a date.
            yearMonthDay = payment.cc_expiration.split(' ')[0].split('-')
            _date = date(int(yearMonthDay[0]), 
                         int(yearMonthDay[1]), 
                         int(yearMonthDay[2]))
            expiration_date = _date.strftime('%m%y')
            
        options = dict(
            amount = str(amount),
            card_num = payment.credit_card,
            last_name = payment.name_on_card,
            phone     = payment.bill_phone_number,
            exp_date = expiration_date,
            address = billing.bill_first_line,
            city = billing.bill_city,
            state = billing.bill_state,
            zip = billing.bill_postal_code,
            invoice_num = order_id,
            description = contact_fields
            )

        result = self.processor.authorize( **options )
        
        # result.response may be
        # - approved
        # - error
        # - declined
        # - held for review
        #
        # Other result fields:
        #   result.response_reason
        #   result.approval_code
        #   result.trans_id

        if result.response == SUCCESS:
            if self.is_recurring_order(order):
                # if a recurring order, then we need to void the transaction
                # (we do the authorization to make sure we have valid CC info)
                # and create a subscription instead
                self.processor.void(trans_id = result.trans_id)
                return self.create_subscription(order, payment)
            else:
                annotation = IAnnotations( order )
                annotation[ interfaces.keys.processor_txn_id ] = result.trans_id
                annotation[ LAST_FOUR ] = payment.credit_card[-4:]
                annotation[ APPROVAL_KEY ] = result.approval_code
                order.user_payment_info_trans_id = result.trans_id

            return interfaces.keys.results_success

        return result.response_reason

    def capture( self, order, amount ):

        annotations = IAnnotations( order )
        trans_id = annotations[ interfaces.keys.processor_txn_id ]
        if self.is_recurring_order(order):
            # creation of subscriptions for recurring orders happens in ``authorize``
            success = True
        else:
            approval_code = annotations[ APPROVAL_KEY ]
            result = self.processor.captureAuthorized(
                amount = str(amount),
                trans_id = trans_id,
                approval_code = approval_code,
                )
            success = result.response == SUCCESS

        if success:
            annotation = IAnnotations( order )
            if annotation.get( interfaces.keys.capture_amount ) is None:
                annotation[ interfaces.keys.capture_amount ] = amount
            else:
                annotation[ interfaces.keys.capture_amount ] += amount
            return interfaces.keys.results_success

        return result.response_reason
    
    def refund( self, order, amount ):

        if self.is_recurring_order(order):
            return 'Refunds for recurring orders are not currently supported.'

        annotations = IAnnotations( order )
        trans_id = annotations[ interfaces.keys.processor_txn_id ]
        last_four = annotations[ LAST_FOUR ]
        
        result = self.processor.credit(
            amount = str( amount ),
            trans_id = trans_id,
            card_num = last_four
            )
        
        if result.response == SUCCESS:
            annotation = IAnnotations( order )
            if annotation.get( interfaces.keys.capture_amount ) is not None:
                annotation[ interfaces.keys.capture_amount ] -= amount
            return interfaces.keys.results_success
        
        return result.response_reason
    
    def create_subscription(self, order, payment):
        if not self.is_recurring_order(order):
            return 'Order does not have a recurring line item.'
        item = order.shopping_cart.values()[0]

        billing = order.billing_address
        amount = order.getTotalPrice()
        contact = order.contact_information
        order_id = order.getOrderId()
        contact_fields = 'Contact Name: ' + contact.name + \
                         ';  Contact Phone: ' + contact.phone_number  + \
                         ';  Contact Email: ' + contact.email

        today = strftime("%Y-%m-%d", gmtime())

        options = dict(
            refId = order_id,
            subscription = {
                'name': order_id,
                'paymentSchedule': {
                    'interval': {
                        'length': item.frequency,
                        'unit': item.unit, },
                    'startDate': today,
                    'totalOccurrences': item.total_occurrences,
                    'trialOccurrences': 0, },
                'order': {
                    'invoiceNumber': order_id,
                    'description': contact_fields,
                    },
                'amount': str(amount),
                'trialAmount': '0',
                'payment': {
                    'creditCard': {
                        'cardNumber': payment.credit_card,
                        'expirationDate': payment.cc_expiration.strftime('%Y-%m'),
                        'cardCode': payment.cc_cvc, },
                    },
                'customer': {
                    'email': contact.email,
                    'phoneNumber': contact.phone_number,
                    },
                'billTo': {
                    'firstName': payment.name_on_card.rsplit(' ', 1)[0],
                    'lastName': payment.name_on_card.rsplit(' ', 1)[1],
                    'address': billing.bill_first_line,
                    'city': billing.bill_city,
                    'state': billing.bill_state,
                    'zip': billing.bill_postal_code },
                },
            )
        result = self.arb_processor.create( **options )

        # result.response may be
        # - approved
        # - error
        # - declined
        # - held for review
        #
        # Other result fields:
        #   result.response_reason
        #   result.approval_code
        #   result.trans_id

        if result['messages']['resultCode'] == 'Ok':
            annotation = IAnnotations( order )
            annotation[ interfaces.keys.processor_txn_id ] = result['subscriptionId']
            annotation[ LAST_FOUR ] = payment.credit_card[-4:]
            order.user_payment_info_trans_id = result['subscriptionId']
            return interfaces.keys.results_success

        return result['messages']['message']['text']

    
    def cancel_subscription(self, order):
        if not self.is_recurring_order(order):
            return 'Order does not have a recurring line item.'
        
        annotations = IAnnotations(order)
        subscriptionId = annotations[interfaces.keys.processor_txn_id]
        
        result = self.arb_processor.cancel(subscriptionId = subscriptionId)
        if result['messages']['resultCode'] == 'Ok':
            del annotations[interfaces.keys.processor_txn_id]
            return interfaces.keys.results_success
        
        return result['messages']['message']['text']
    
    @property
    def processor( self ):
        options = IAuthorizeNetOptions(self.context)
        server = self._sites.get(options.server_url)
        cc = CcProcessor(server=server,
                         login=options.merchant_id,
                         key=options.merchant_key)
        return cc

    @property
    def arb_processor(self):
        options = IAuthorizeNetOptions(self.context)
        server = self._arb_sites.get(options.server_url)
        arb = ARBProcessor(server=server,
                           login=options.merchant_id,
                           key=options.merchant_key)
        return arb
