#
from getpaid.core.options import PersistentOptions
import interfaces

AuthorizeNetOptions = PersistentOptions.wire(
                           "AuthorizeNetOptions",
                           "getpaid.authorizedotnet",
                           interfaces.IAuthorizeNetOptions)
