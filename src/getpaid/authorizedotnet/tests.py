from zope.testing import doctest, renormalizing
import os
import re
import unittest

def remoteSetUp(test):
    login = os.environ.get('AUTHORIZE_DOT_NET_LOGIN')
    key = os.environ.get('AUTHORIZE_DOT_NET_TRANSACTION_KEY')

    if login is None or key is None:
        raise RuntimeError('both AUTHORIZE_DOT_NET_LOGIN and'
                           ' AUTHORIZE_DOT_NET_TRANSACTION_KEY must be'
                           ' provided in order to run the zc.authorizedotnet'
                           ' tests against the Authorize.Net test server.')

    test.globs['LOGIN'] = login
    test.globs['KEY'] = key

def test_suite():
    checker = renormalizing.RENormalizing([
        (re.compile(r"'.{6}'"), "'123456'"), # for approval codes
        (re.compile(r"'\d{9}'"), "'123456789'"), # for transaction IDs
        ])

    arb = doctest.DocFileSuite(
            'subscription.txt',
            globs = dict(
                SERVER_NAME='apitest.authorize.net',
                ),
            optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS,
            checker = checker,
            setUp = remoteSetUp,
            )
    arb.level = 5
    return unittest.TestSuite(arb)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
