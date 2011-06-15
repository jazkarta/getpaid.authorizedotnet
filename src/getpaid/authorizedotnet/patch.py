import os.path
import httplib
import zc.ssl

from zc.authorizedotnet.processing import AuthorizeNetConnection
from zc.authorizedotnet.processing import TransactionResult

def sendTransaction(self, **kws):
    # if the card number passed in is the "generate an error" card...
    if kws.get('card_num') == '4222222222222':
        # ... turn on test mode (that's the only time that card works)
        kws['test_request'] = 'TRUE'

    body = self.formatRequest(kws)

    if self.server.startswith('localhost:'):
        server, port = self.server.split(':')
        conn = httplib.HTTPConnection(server, port)
    else:
        cert_file = os.path.join(os.path.dirname(__file__), "certs.pem")
        conn = zc.ssl.HTTPSConnection(self.server, timeout=self.timeout, cert_file=cert_file)
    conn.putrequest('POST', '/gateway/transact.dll')
    conn.putheader('content-type', 'application/x-www-form-urlencoded')
    conn.putheader('content-length', len(body))
    conn.endheaders()
    conn.send(body)

    response = conn.getresponse()
    fields = response.read().split(self.delimiter)
    result = TransactionResult(fields)
    
    if (self.salt is not None
    and not result.validateHash(self.login, self.salt)):
        raise ValueError('MD5 hash is not valid (trans_id = %r)'
                         % result.trans_id)

    return result
AuthorizeNetConnection.sendTransaction = sendTransaction
