GetPaid Authorize.Net Payment Processor
=======================================


Store Specific Processor Setting Tests
--------------------------------------

First let's create a store class to work with:
      
      >>> from getpaid.core import interfaces 
      >>> from zope.app.annotations import IAttributeAnnotatable
      >>> from zope.interface import implements
      >>> class Store:
      ...    implements( interfaces.IStore, IAttributeAnnotatable )
      >>> store = Store()

And configure our payment processor:

      >>> interfaces.I
      >>

Now let's create an order to process:

      >>> from getpaid.core import order, item, cart
      >>> order1 = order.Order()
      >>> my_cart = cart.ShoppingCart()
      >>> my_cart['abc'] = abc = item.LineItem()
      >>> abc.cost = 22.20; abc.name = 'abc'; abc.quantity = 3
      >>> str(order1.getTotalPrice())
      '22.20'

Authorizing an Order
--------------------       

Now we can run it through a processor:
    
      >>> from zope import component
      >>> processor = IPaymentProcessor( store )
      >>> processor.authorize( order ) == interfaces.keys.results_sucess
      True
      >>> 

Capturing/Charing an Order
--------------------------

Refunding an Order
------------------


Voiding an Order
----------------
    

      
      




