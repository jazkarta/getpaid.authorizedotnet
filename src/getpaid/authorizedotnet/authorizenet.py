"""
$Id: $
"""

from zope import interface
from zope.component import getUtility, getAdapter

from hurry.workflow.interfaces import IWorkflowInfo

from getpaid.core.interfaces import IPaymentProcessor
from zc.authorizedotnet.processing import CcProcessor

from interfaces import IAuthorizeNetOptions

# XXX need to get the correct transition mappings here

_reason_to_transition = {
    "approved": "authorize",
    "error": "processor-cancelled",
    "declined": "processor-cancelled",
    }

_sites = {
    "Production": "secure.authorize.net:443",
    "Sandbox": "test.authorize.net:443")


class AuthorizeNetAdapter(object):
    interface.implements(IPaymentProcessor)

    options_interface = IAuthorizeNetOptions

    def __init__(self, context):
        self.context = context

    def authorize(self, order, payment):
        options = IAuthorizeNetOptions(self.context)

        server = _sites.get(options.server_url)
        cc = CcProcessor(server=options.server,
                         login=options.merchant_id,
                         key=options.merchant_key)

        
        billing = order.billing_address
        amount = order.getTotalPrice()

        # TODO:  also send login id as x_cust_id
        result = cc.authorize(
            amount=str(amount),
            card_num=payment.credit_card,
            exp_date=payment.cc_expiration,
            address=billing.bill_first_line,
            city=billing.bill_city,
            state=billing.bill_state,
            zip=billing.bill_postal_code
            )
        # result.response may be
        # - approved
        # - error
        # - declined
        # - held for review
        #
        # Other result fields:
        #   result.response_reason
        #   result.approval_code
        #   result.trans_id
        reason = result.response_reason
        order.processor_order_id = result.trans_id
        
        # XXX the response_reason should go into the order instead of the
        # XXX workflow once the order supportse that
        transition = _reason_to_transition.get( reason )
        if transition:
            order.finance_workflow.fireTransition( transition,
                                                   comment=result.response_reason)
            
