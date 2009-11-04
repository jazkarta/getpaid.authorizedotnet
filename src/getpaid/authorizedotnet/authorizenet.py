# Copyright (c) 2007 ifPeople, Juan Pablo Giménez, and Contributors
"""

notes on error handling, if we haven't talked to the processor then raise an exception,
else return an error message so higher levels can interpret/record/notify user/etc.

$Id: $
"""
from time import time
import hmac
import random
from cPickle import loads, dumps

from AccessControl import getSecurityManager
from zope import interface, schema
from zope.component import getUtility, getAdapter
from zope.app.annotation.interfaces import IAnnotations
from zope.app.component.hooks import getSite

from zc.authorizedotnet.processing import CcProcessor
from getpaid.core import interfaces, payment
from getpaid.core.processors import OffsitePaymentProcessor
from getpaid.core.interfaces import IShoppingCartUtility, IOrderManager, \
                                    ILineContainerTotals
from getpaid.core.order import Order as BaseOrder

from interfaces import IAuthorizeNetOptions
from datetime import date

SUCCESS = 'approved'
DEFAULT_SHOW_FORM = 'PAYMENT_FORM'
DEFAULT_METHOD = 'CC'
DEFAULT_LINK_METHOD='POST'
DEFAULT_LINK_TEXT='Return to our online store'

# needed for refunds
LAST_FOUR = "getpaid.authorizedotnet.cc_last_four"

APPROVAL_KEY = "getpaid.authorizedotnet.approval_code"

_offsite_hosts = dict(
    Production = "https://secure.authorize.net:443/gateway/transact.dll",
    Test = "https://test.authorize.net:443/gateway/transact.dll"
)

class AuthorizeNetAdapter(object):
    interface.implements( interfaces.IPaymentProcessor )

    options_interface = IAuthorizeNetOptions

    _sites = dict(
        Production = "secure.authorize.net:443",
        Test = "test.authorize.net:443"
        )

    def __init__(self, context):
        self.context = context

    def authorize(self, order, payment):

        billing = order.billing_address
        amount = order.getTotalPrice()
        contact = order.contact_information
        order_id = order.getOrderId()
        contact_fields = 'Contact Name: ' + contact.name + ';  Contact Phone: ' + contact.phone_number  + ';  Contact Email: ' + contact.email

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
        approval_code = annotations[ APPROVAL_KEY ]
        
        result = self.processor.captureAuthorized(
            amount = str(amount),
            trans_id = trans_id,
            approval_code = approval_code,
            )

        if result.response == SUCCESS:
            annotation = IAnnotations( order )
            if annotation.get( interfaces.keys.capture_amount ) is None:
                annotation[ interfaces.keys.capture_amount ] = amount
            else:
                annotation[ interfaces.keys.capture_amount ] += amount            
            return interfaces.keys.results_success

        return result.response_reason
    
    def refund( self, order, amount ):

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
    
    @property
    def processor( self ):
        options = IAuthorizeNetOptions(self.context)
        server = self._sites.get(options.server_url)
        cc = CcProcessor(server=server,
                         login=options.merchant_id,
                         key=options.merchant_key)
        return cc

class IOffSiteProcessorSchema(interface.Interface):
    x_login = schema.TextLine()
    x_amount = schema.TextLine()
    x_fp_sequence = schema.TextLine()
    x_fp_timestamp = schema.TextLine()
    x_fp_hash = schema.TextLine()
    x_show_form = schema.TextLine()
    x_method = schema.TextLine()
    x_receipt_link_method = schema.TextLine()
    x_receipt_link_text = schema.TextLine()
    x_receipt_link_URL = schema.TextLine()
    x_invoice_num = schema.TextLine()

class IOffsiteOrder(interfaces.IOrder):
    """
    """
    
class Order(BaseOrder):
    """
    """
    interface.implements(IOffsiteOrder)

class OffSiteProcessor(OffsitePaymentProcessor):
    interface.implements(IOffSiteProcessorSchema)
    
    name = 'getpaid.authorizedotnet.offsite_processor'
    title = u'Off-site authorize.net Checkout'
    options_interface = IAuthorizeNetOptions

    checkout_button = 'getpaid.authorizedotnet.checkout-button'

    def __init__(self, cart):
        super(OffsitePaymentProcessor, self).__init__(cart)
        self.options = self.options_interface(getSite())
        self.x_fp_sequence = random.randrange(0, 999, 1)
        self.x_fp_timestamp = ("%s" % time()).split(".")[0]

    def server_url(self):
        return _offsite_hosts[getattr(self.options, "authorizedotnet_server_url", "Test")]

    @property
    def x_login(self):
        return getattr(self.options, "login_id", "")

    @property
    def x_amount(self):
        cartutil=getUtility(IShoppingCartUtility)
        cart=cartutil.get(getSite())
        total = ILineContainerTotals(cart).getTotalPrice()
        return '%.2f' % total

    @property
    def x_fp_hash(self):
        fingerprint = "%s^%s^%s^%s^" % (self.x_login,
                                        self.x_fp_sequence,
                                        self.x_fp_timestamp,
                                        self.x_amount)
        return hmac.new(self.options.transaction_key,fingerprint).hexdigest()
    
    @property
    def x_show_form(self):
        return DEFAULT_SHOW_FORM
    
    @property
    def x_method(self):
        return DEFAULT_METHOD

    @property
    def x_receipt_link_method(self):
        return DEFAULT_LINK_METHOD
    
    @property
    def x_receipt_link_text(self):
        return DEFAULT_LINK_TEXT

    @property
    def x_receipt_link_URL(self):
        return getSite().absolute_url() + '/@@getpaid.authorizedotnet.ipnreactor'

    @property
    def x_invoice_num(self):
        cartutil=getUtility(IShoppingCartUtility)
        cart=cartutil.get(getSite())
        # we'll get the order_manager, create the new order, and store it.
        order_manager = getUtility(IOrderManager)
        new_order_id = order_manager.newOrderId()
        order = Order()
        
        # register the payment processor name to make the workflow handlers happy
        order.processor_id = 'getpaid.authorizedotnet.processor'

        # FIXME: registering an empty contact information list for now - need to populate this from user
        # if possible
        order.contact_information = payment.ContactInformation()
        order.billing_address = payment.BillingAddress()
        order.shipping_address = payment.ShippingAddress()

        order.order_id = new_order_id
        
        # make cart safe for persistence by using pickling
        order.shopping_cart = loads(dumps(cart))
        order.user_id = getSecurityManager().getUser().getId()

        order.finance_workflow.fireTransition('create')
        order.finance_workflow.fireTransition('authorize')
        
        order_manager.store(order)

        return order.order_id

class FinanceProcessorIntegration(payment.DefaultFinanceProcessorIntegration):

    def __call__( self, event ):
        # processor is async, so just return
        return
