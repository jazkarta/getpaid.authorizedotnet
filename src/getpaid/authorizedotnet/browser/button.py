from time import time
import hmac
import random
from cPickle import loads, dumps

from AccessControl import getSecurityManager
from zope.app.component.hooks import getSite
from zope.component import getUtility

from getpaid.core import interfaces
from getpaid.core import payment
from getpaid.core.order import Order
from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions
from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility, queryAdapter, adapts
from zope.app.component.hooks import getSite
from zope import interface, schema

from z3c.form import form, field, button
from z3c.form.interfaces import IFormLayer, HIDDEN_MODE
from plone.z3cform.layout import FormWrapper, wrap_form
from plone.z3cform import z2
from Products.Five.browser import BrowserView

from getpaid.core.interfaces import IShoppingCartUtility, IOffsitePaymentProcessor

from getpaid.authorizedotnet.interfaces import IAuthorizeNetOptions
from getpaid.authorizedotnet.authorizenet import IOffSiteProcessorSchema

class View(BrowserView):
    
    def __init__(self, context, request):
        super(BrowserView, self).__init__(context, request)
        self.sequence = random.randrange(0, 999, 1) 
        self.timestamp = ("%s" % time()).split(".")[0]
        
    def getOpt(self, option):
        portal = getSite()
        options = IAuthorizeNetOptions(portal)
        return getattr(options, option)

    def proceed_url(self):
        return self.context.absolute_url() + '/@@getpaid-authdotnet-smi-checkout-proceed'

    def server_url(self):
        return self.context.server_url
    
    def receipt_link_url(self):
        return self.context.absolute_url() + '/@@getpaid-authdotnet-smi-receipt'

    def merchant_id(self):
        return self.getOpt('merchant_id')

    def merchant_key(self):
        return self.getOpt('merchant_key')

    def amount(self):
        cart = getUtility(interfaces.IShoppingCartUtility).get(self.context)
        return interfaces.ILineContainerTotals(cart).getTotalPrice()

    def hash(self):
        fingerprint = "%s^%s^%s^%s^" % (self.merchant_id(),
                                          self.sequence,
                                          self.timestamp,
                                          self.amount())
        return hmac.new(self.merchant_key(),fingerprint).hexdigest()
    
    def order_id(self):
        cart_util = getUtility(interfaces.IShoppingCartUtility)
        cart = cart_util.get(self.context, create=True)
        site = getSite()
        manage_options = IGetPaidManagementOptions( site )
        
        # we'll get the order_manager, create the new order, and store it.
        order_manager = getUtility(interfaces.IOrderManager)
        new_order_id = order_manager.newOrderId()
        order = Order()
        
        # register the payment processor name to make the workflow handlers happy
        order.processor_id = manage_options.payment_processor
        
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
        
        order_manager.store(order)

        # have to wait for the order to be created and the cart added for this to work
        order.finance_workflow.fireTransition('authorize')

        # and destroy the cart
        cart_util.destroy(self.context)

        return order.order_id
        
class ButtonForm(form.Form):
    fields = field.Fields(IOffSiteProcessorSchema, mode = HIDDEN_MODE)
    ignoreRequest = True # don't use request to get widget data
#    label = u"hidden form"
    prefix = '' # external processor needs unprefixed fields

    @button.buttonAndHandler(u'Authorize.net Checkout')
    def handlePay(self, action):
        # Action points to external processor
        # so this code is never reached...
        pass
    
class Widgets(field.FieldWidgets):
    adapts(ButtonForm, IFormLayer, interface.Interface)
    
    prefix = '' # NMI external processor needs unprefixed fields
    
class ButtonWrapper(FormWrapper):
    """page for button view
    """

    def __init__(self, context, request):
        super(ButtonWrapper, self).__init__(context, request)
        cartutil=getUtility(IShoppingCartUtility)
        cart=cartutil.get(getSite(), create=True)
        self.processor = queryAdapter(cart, IOffsitePaymentProcessor,
                                      'getpaid.authorizedotnet.processor')
        
    def contents(self):
        """This is the method that'll call your form.  You don't
        usually override this.
        """
        # A call to 'switch_on' is required before we can render
        # z3c.forms within Zope 2.
        z2.switch_on(self, request_layer=self.request_layer)
        self.request.getURL = self.processor.server_url
        return self.render_form()

    def enabled(self):
        return self.processor.x_login

ButtonView = wrap_form(ButtonForm, ButtonWrapper)
