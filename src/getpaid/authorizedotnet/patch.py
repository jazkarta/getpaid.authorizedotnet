import httplib

try:
    from zope.app.component.hooks import getSite
except ImportError:
    from zope.site.hooks import getSite

from getpaid.authorizedotnet.interfaces import IAuthorizeNetOptions

from zc.authorizedotnet.processing import AuthorizeNetConnection
from zc.authorizedotnet.processing import TransactionResult


TEST_CARDS = (
    '4222222222222',
    '4007000000027',
    '4012888818888',
    '370000000000002',
    '6011000000000012',
    )


def sendTransaction(self, **kws):
    site = getSite()
    options = IAuthorizeNetOptions(site)
    
    # if the card number passed in is the "generate an error" card...
    if options.send_test_requests and kws.get('card_num') in TEST_CARDS:
        # ... turn on test mode
        kws['test_request'] = 'TRUE'

    body = self.formatRequest(kws)

    if self.server.startswith('localhost:'):
        server, port = self.server.split(':')
        conn = httplib.HTTPConnection(server, port)
    else:
        conn = httplib.HTTPSConnection(self.server, timeout=self.timeout)
    conn.putrequest('POST', '/gateway/transact.dll')
    conn.putheader('content-type', 'application/x-www-form-urlencoded')
    conn.putheader('content-length', len(body))
    conn.endheaders()
    conn.send(body)

    response = conn.getresponse()
    full_response = response.read()
    fields = full_response.split(self.delimiter)
    result = TransactionResult(fields)
    result.full_response = full_response
    
    if (self.salt is not None
    and not result.validateHash(self.login, self.salt)):
        raise ValueError('MD5 hash is not valid (trans_id = %r)'
                         % result.trans_id)

    return result
AuthorizeNetConnection.sendTransaction = sendTransaction
