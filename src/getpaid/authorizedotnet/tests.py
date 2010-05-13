from zope.testing import doctest, renormalizing
from zope.testing.doctestunit import DocFileSuite
from zope.app.testing import placelesssetup
from zope.component import provideUtility
from Products.Five import zcml
import os
import re
import unittest

def remoteSetUp(test):
    placelesssetup.setUp()
    from getpaid.core.interfaces import ITaxUtility
    from getpaid.core.tax import TaxUtility
    provideUtility(TaxUtility(), ITaxUtility)
    import Products.Five
    import getpaid.authorizedotnet
    zcml.load_config('configure.zcml', Products.Five)
    zcml.load_config('configure.zcml', getpaid.authorizedotnet)
    
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

    suites = []
    for testfile in ['authorizenet.txt', 'subscription.txt']:
        suite = DocFileSuite(
            testfile,
            globs = dict(
                SERVER_NAME='apitest.authorize.net',
                ),
            optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS,
            checker = checker,
            setUp = remoteSetUp,
            tearDown = placelesssetup.tearDown,
            )
        suites.append(suite)
    return unittest.TestSuite(suites)
