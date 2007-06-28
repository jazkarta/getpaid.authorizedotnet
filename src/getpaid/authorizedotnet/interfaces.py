"""
"""

from zope import schema
from getpaid.core import interfaces

class IAuthorizeNetOptions(interfaces.IPaymentProcessorOptions):
    """
    Authorize.Net options
    """
    server_url = schema.Choice(
        title=u"Authorize.net Server URL",
        values=("https://secure.authorize.net/gateway/transact.dll",))
    merchant_id = schema.TextLine(
        title=u"Merchant Id")
    merchant_key = schema.ASCII(
        title=u"Merchant Key")
