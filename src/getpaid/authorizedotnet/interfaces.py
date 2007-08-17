"""
"""

from zope import schema, interface
from getpaid.core import interfaces

class IAuthorizeNetOrder( interface.Interface ):
    """ in future use annotation for processor specific options """


class IAuthorizeNetOptions(interfaces.IPaymentProcessorOptions):
    """
    Authorize.Net options
    """
    server_url = schema.Choice(
        title=u"Authorize.net Server URL",        
        values=("Test",
                "Production")
        )
    merchant_id = schema.ASCIILine( title=u"API Login Id" )
    merchant_key = schema.ASCIILine( title=u"Transaction Key" )
        
