"""
$Id: $
"""

import interfaces
from getpaid.core.options import PersistentOptions


AuthorizeNetOptions = PersistentOptions.wire(
                           "AuthorizeNetOptions",
                           "getpaid.authorizedotnet",
                           interfaces.IAuthorizeNetOptions)
