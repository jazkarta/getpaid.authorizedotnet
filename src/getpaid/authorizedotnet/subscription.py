import httplib
try:
    from xml.etree import ElementTree
except ImportError:
    # Python < 2.5
    from elementtree import ElementTree
import zc.ssl

# ARB expects request parameters in a particular order
REQUEST_KEY_ORDER = ("merchantAuthentication refId subscriptionId subscription name transactionKey "
                     "paymentSchedule interval length unit "
                     "startDate totalOccurrences trialOccurrences amount trialAmount "
                     "payment creditCard cardNumber expirationDate cardCode bankAccount "
                     "accountType routingNumber accountNumber nameOnAccount echeckType "
                     "bankName order invoiceNumber description customer id email "
                     "phoneNumber faxNumber billTo firstName lastName company address "
                     "city state zip country shipTo".split())

def arb_request_key_order(i):
    try:
        return REQUEST_KEY_ORDER.index(i[0])
    except ValueError:
        raise Exception('Unexpected ARB request key: %s' % i[0])

def xmlify_dict(d, indent=0):
    s = ''
    for k, v in sorted(d.items(), key=arb_request_key_order):
        if isinstance(v, dict):
            v = '\n' + xmlify_dict(v, indent + 2) + ' ' * indent
        s += '%s<%s>%s</%s>\n' % (' ' * indent, k, v, k)
    return s

def dictify_etree_node(node):
    d = {}
    for child in node:
        d[child.tag[child.tag.index('}') + 1:]] = dictify_etree_node(child)
    return d or node.text.strip()

class ARBConnection(object):

    def __init__(self, server, login, key, salt=None, timeout=None):
        self.server = server
        self.login = login
        self.salt = salt
        self.timeout = timeout
        self.key = key
        self.authentication = {
            'name': self.login,
            'transactionKey': self.key
            }

    def sendTransaction(self, method, **kw):
        kw['merchantAuthentication'] = self.authentication
        
        xml = """<?xml version="1.0" encoding="utf-8"?>
<%s xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd">
%s
</%s>
""" % (method, xmlify_dict(kw), method)
        
        if self.server.startswith('localhost:'):
            server, port = self.server.split(':')
            conn = httplib.HTTPConnection(server, port)
        else:
            conn = zc.ssl.HTTPSConnection(self.server,
                                          timeout=self.timeout)
        conn.putrequest('POST', '/xml/v1/request.api')
        conn.putheader('content-type', 'text/xml')
        conn.putheader('content-length', len(xml))
        conn.endheaders()
        conn.send(xml)

        response = conn.getresponse()
        root = ElementTree.parse(response).getroot()
        return dictify_etree_node(root)


class ARBProcessor(object):
    def __init__(self, server, login, key, salt=None, timeout=None):
        self.connection = ARBConnection(server, login, key, salt, timeout)

    def create(self, **kw):
        if not isinstance(kw['subscription']['amount'], basestring):
            raise ValueError('Subscription amount must be a string')
        if not isinstance(kw['subscription'].get('trialAmount', ''), basestring):
            raise ValueError('Subscription trialAmount must be a string')

        return self.connection.sendTransaction('ARBCreateSubscriptionRequest', **kw)

    def update(self, **kw):
        return self.connection.sendTransaction('ARBUpdateSubscriptionRequest', **kw)

    def cancel(self, **kw):
        return self.connection.sendTransaction('ARBCancelSubscriptionRequest', **kw)
