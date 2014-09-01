'''
Support for observable parameters.
When using :class:`Observable` it is possible to register observers
for notifications (callbacks) on change of data values.

The implementation is thread safe by using python threading locks. 
'''

import exceptions
from functools import wraps
import threading  # for lock
import weakref

def threadsafe( lockname ):
    """A decorator to acquire and release a lock around a method call.
    
    Use this to provide thread safe implementation of methods. It is not necessarily
    the most efficient use of locking, but for simple cases it does the job in an
    unintrusive fashion.
    """
    def _synched(func):
        @wraps(func)
        def _synchronizer(self,*args, **kwargs):
            lock = self.__getattribute__( lockname )
            lock.acquire()
            try:
                return func( self, *args, **kwargs )
            finally:
                lock.release()
        return _synchronizer
    return _synched

class RecursionError(exceptions.RuntimeError):
    pass


class Observable(object):
    """An observable implemented as a `python Descriptor <https://docs.python.org/2/howto/descriptor.html>`_.
    
    Use the :func:`Observable.subscribe` to register for notification updates. 

    :note: The business logic is deferred to the :class:`Observable.__ObservableValue__` class
           in :obj:`self.observable_value`.
    """
    def __init__(self, name):
        self.var_name = "__"+name
        self.observable_value = Observable.__ObservableValue__

    def __set__(self,inst, value ):
        '''set gets the instances associated variable and calls 
        its setvalue method, which notifies subribers'''
        if inst and not hasattr(inst, self.var_name):
            setattr(inst, self.var_name, self.observable_value())
        ov = getattr(inst, self.var_name)
        ov.setvalue(value)

    def __get__(self, inst, cls):
        '''Get the instances associated variable :class:`Observable.__ObservableValue__`'''
        if inst and not hasattr(inst, self.var_name):
            setattr(inst, self.var_name, self.observable_value())
        return getattr(inst, self.var_name)
    
    def subscribe(self, obsv, exception_handler = None):
        '''Add a subscriber to be notified on change of value in the Observable.
        
        :param obsv: Observer to be notified of change.
        :type obsv: a callable or another :class:`Observable` object. 
            The callable must accept one argument which is the updated value.
        
        :param exception_handler: An exception handler or None
        :type exception_handler: callable with one argument which is the raised exception
        
        :rtype: :class:`Observable._NotifySubscription` object. Hang on to this object
            for as long as notification updates are required. When this object is finalised,
            the notification updates will be cancelled.
        '''
        # This func is really just here as a place holder in the docs.
        # Because this class is a python Descriptor it refers all dereferncing
        # through the __get__ function which in turns uses the __ObservableValue__
        # object in getattr(self, self.var_name).
        raise NotImplementedError

    class __ObservableValue__(object):
        '''Private class, used only by :class:`Observable` 
        
        Handle subscribers to update notifcations.'''
        
    
        def __init__(self):
            self.subscribers = []
            self._value = None
            self._change_lock = threading.Lock()
            self._sync_lock = threading.RLock()
            
        def __call__(self):
            """ Make class callable.
            
            @return: the current data value
            """
            return self._value
    
        def _notify_subscribers(self, value):
            for (f,exception_handler) in self._callbacks():
                try:
                    f(value)
                except Exception, ex:
                    if exception_handler and not exception_handler(ex): 
                        raise            # reraise if not handled
    
        @threadsafe('_sync_lock')
        def setvalue(self, value):
            """Notify the subcribers only when the value changes."""
            if self._value != value:
                if self._change_lock.acquire(0):     # non-blocking
                    self._value = value
                    try:
                        self._notify_subscribers(value)
                    finally:
                        self._change_lock.release()
                else:
                    raise RecursionError("Attempted recursion into observable's set method.")
    
        @threadsafe('_sync_lock')
        def subscribe(self, obsv, exception_handler = None):
            '''subscribe(self, obsv, exception_handler = None)
        
            Add a subscriber to be notified on change of value in the Observable.
            
            :param obsv: Observer to be notified of change.
            :type obsv: a callable or another :class:`Observable` object. 
                The callable must accept one argument which is the updated value.
            
            :param exception_handler: An exception handler or None
            :type exception_handler: callable with one argument which is the raised exception
            
            :rtype: :class:`Observable._NotifySubscription` object. Hang on to this object
                for as long as notification updates are required. When this object is finalised,
                the notification updates will be cancelled.
            '''
            observer = obsv.setvalue if isinstance(obsv, Observable.__ObservableValue__) else obsv
            ob_info =(observer, exception_handler)
            self.subscribers.append(ob_info)
            return Observable._NotifySubscription(ob_info, self)
    
        @threadsafe('_sync_lock')
        def _callbacks(self):
            scribers = []
            scribers.extend(self.subscribers)
            return scribers
    
        @threadsafe('_sync_lock')
        def _cancel(self, wref):
            self.subscribers.remove(wref)
    
    class _NotifySubscription(object):
        '''A subscription class which cancels the notifications to the subscriber
           when instances of this class are finalised.
           
           There is no need to directly instansiate or operate on insatances of this class.
           '''
        def __init__(self, subscriber, observable):
            self.subscriber = subscriber
            self.observed = weakref.ref(observable)
        def __del__(self):
            obsrvd = self.observed()
            if (self.subscriber and obsrvd):
                obsrvd._cancel(self.subscriber)


#-----------------------------------------------------------------------
#   Example & Simple Test
#-----------------------------------------------------------------------
if __name__ == '__main__':

    class MyClass(object):
        """ A Class containing the observables length and width"""
        length = Observable('length')
        width = Observable('width')

        def __init__(self):
            #self.length = Observable('length')
            #self.width = Observable('width')
            self.length.setvalue(0)
            self.width.setvalue(0)
            

    class MyObserver(object):
        """An observer class. The initializer is passed an instance
           of 'myClass' and subscribes to length and width changes.
           This observer also itself contains an observable, l2"""
        
        l2 = Observable('l2')

        def __init__(self, name, observedObj):
            self.name = name
            self.subs1 = observedObj.length.subscribe(self.print_l)
            self.subs2 = observedObj.width.subscribe(self.print_w)
            
            """An observable can subscribe to an observable, in which case
              a change will chain through both subscription lists.
              Here l2's subscribers will be notified whenever observedObj.length
              changes"""
            self.subs3 = observedObj.length.subscribe(self.l2)

        def print_w(self, value):
            print "%s Observed Width"%self.name, value

        def print_l(self, value):
            print "%s Observed Length"%self.name, value
            
        def cancel(self):
            """Cancels the instances current subscriptions. Setting self.subs1 to
            None removes the reference to the subscription object, causing it's 
            finalizer (__del__) method to be called."""
            self.subs1 = None
            self.subs2 = None
            self.subs3 = None

    def pl2(value):
        print "PL2 reports ", value
        if type(value) == type(3):
            raise ValueError("pl2 doesn't want ints.")

    def handlePl2Exceptions( ex ):
        print 'Handling pl2 exception:', ex, type(ex)
        return True     # true if handled, false if not
            
    area = MyClass()
    kent = MyObserver("Kent", area)
    billy = MyObserver("Billy", area)
    subscription = billy.l2.subscribe(pl2, handlePl2Exceptions)

    blah = MyClass()
    s = MyObserver("BLAH", blah)
    blah.length = 2
    
    area.length = 6
    area.width = 4
    area.length = "Reddish"

    billy.subs1 = None
    print "Billy shouldn't report a length change to 5.15."
    area.length = 5.15      
    billy.cancel()
    print "Billy should no longer report"
    area.length = 7
    area.width = 3
    print "Areas values are ", area.length(), area.width()

    print "Deleting an object with observables having subscribers is ok"
    area = None
    area = MyClass()
    print "replaced area - no subscribers to this new instance"
    area.length = 5
    area.width ="Bluish"
    c = raw_input("ok? ")



