from zope.component import getUtility, queryAdapter, adapts
from zope.app.component.hooks import getSite
from zope import interface, schema

from z3c.form import form, field, button
from z3c.form.interfaces import IFormLayer, HIDDEN_MODE
from plone.z3cform.layout import FormWrapper, wrap_form
from plone.z3cform import z2
from Products.Five.browser import BrowserView

from getpaid.core.interfaces import IShoppingCartUtility, IOffsitePaymentProcessor

class Thankyou(BrowserView):
    """Class for overriding getpaid-thank-you view
    """
    
    def getInvoice(self):
        if self.request.has_key('orderid'):
            return self.request['orderid']
        else:
            return None

    def getURL(self):
        portal_url = getSite().absolute_url()
        if self.getInvoice() is not None:
            return "%s/@@getpaid-order/%s" % ( portal_url, self.getInvoice())
        else:
            return ''

class Error(Thankyou):
    """Class for checkout errors view
    """
    
    def getCartURL(self):
        portal_url = getSite().absolute_url()
        return "%s/@@getpaid-cart" % portal_url
