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

from getpaid.authorizedotnet.interfaces import IAuthorizeNetOptions

class View(BrowserView):

    def verify(self):
        try:
            import ipdb as pdb
        except: import pdb
        pdb.set_trace()