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
        values=("secure.authorize.net:443",
                "test.authorize.net:443")
        )
    merchant_id = schema.ASCIILine( title=u"API Login Id" )
    merchant_key = schema.ASCIILine( title=u"Transaction Key" )
        
