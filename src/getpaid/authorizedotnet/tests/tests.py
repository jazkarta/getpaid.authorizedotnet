import sys
from IPython.Shell import IPShellEmbed
import unittest
from Testing import ZopeTestCase
from zope.testing import doctest
from Products.PloneGetPaid.tests.base import PloneGetPaidFunctionalTestCase
import Products.PloneGetPaid
import getpaid.authorizedotnet
from Products.Five import zcml
from xml.dom.minidom import parseString


OPTIONFLAGS = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE |
               doctest.REPORT_UDIFF)


class AuthorizedotnetFuncationalTestCase(PloneGetPaidFunctionalTestCase):

    def afterSetUp(self):
        super(AuthorizedotnetFuncationalTestCase, self).afterSetUp()
        zcml.load_config('configure.zcml', package=getpaid.authorizedotnet)
        zcml.load_config('configure.zcml', package=Products.PloneGetPaid)
        self.portal.portal_quickinstaller.installProduct('PloneGetPaid')

    def extract_data(self, xml_blob, name):
        xml = parseString(xml_blob)
        return str(xml.getElementsByTagName(name)[0].firstChild.data).strip()

    def ipython(self, locals=None):
        """Provides an interactive shell aka console inside your testcase. 
        Uses ipython for on steroids shell... 
    
        It looks exact like in a doctestcase and you can copy and paste 
        code from the shell into your doctest. The locals in the testcase are 
        available, becasue you are in the testcase. 
    
        In your testcase or doctest you can invoke the shell at any point by 
        calling:: 
    
            >>> self.ipython( locals() ) 
    
        locals -- passed to InteractiveInterpreter.__init__() 
        """
        savestdout = sys.stdout
        sys.stdout = sys.stderr
        sys.stderr.write('='*70)
        embedshell = IPShellEmbed(argv=[],
                                  banner=""" 
IPython Interactive Console
    
Note: You have the same locals available as in your test-case.
""",
                                  exit_msg="""end of ZopeTestCase Interactive Console session""",
                                  user_ns=locals)
        embedshell()
        sys.stdout.write('='*70+'\n')
        sys.stdout = savestdout

def test_suite():
    return unittest.TestSuite([
        ZopeTestCase.ZopeDocFileSuite(
            'authorizedotnet.txt',
            package='getpaid.authorizedotnet',
            test_class=AuthorizedotnetFuncationalTestCase,
            optionflags=OPTIONFLAGS,
            ),
        ZopeTestCase.ZopeDocFileSuite(
            'authorizedotnet-browser.txt',
            package='getpaid.authorizedotnet',
            test_class=AuthorizedotnetFuncationalTestCase,
            optionflags=OPTIONFLAGS,
            ),
        ZopeTestCase.ZopeDocFileSuite(
            'authorizedotnet-offsite.txt',
            package='getpaid.authorizedotnet',
            test_class=AuthorizedotnetFuncationalTestCase,
            optionflags=OPTIONFLAGS,
            ),
        ])
