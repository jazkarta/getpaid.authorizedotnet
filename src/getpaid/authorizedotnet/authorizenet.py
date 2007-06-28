"""
"""
from zope.component import getUtility, getAdapter
from zc.authorizedotnet.processing import CcProcessor
from decimal import Decimal
from getpaid.core.interfaces import IPaymentProcessor
from zope import interface
from hurry.workflow.interfaces import IWorkflowInfo

from interfaces import IAuthorizeNetOptions

# XXX need to get the correct transition mappings here
_reason_to_transition = {
    "approved": "",
    "error": "",
    "declined": "cancel-declined",
    "held for review": "",
    }

class AuthorizeNetAdapter(object):
    interface.implements(IPaymentProcessor)

    def __init__(self, context):
        self.context = context

    def authorize(self, order, payment):
        options = IAuthorizeNetOptions(self.context)
        cc = CcProcessor(server=options.server_url,
                         login=options.merchant_id,
                         key=options.merchant_key)
        billing = order.billing_address
        amount = order.getTotalAmount()

        result = cc.authorize(amount=str(amount),
                              card_num=payment.credit_card,
                              exp_date=payment.cc_expiration,
                              address=billing.bill_first_line,
                              zip=billing.bill_postal_code)
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
        info = getAdapter(order, IWorkflowInfo, "getpaid.finance.info")
        # XXX the response_reason should go into the order instead of the
        # XXX workflow once the order supports that
        info.fireTransition(_reason_to_transition[reason],
                            comment=result.response_reason)
