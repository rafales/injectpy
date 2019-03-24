Lifetime / scoping
==================

Different class instances are meant to live for different time. For
example we'll want our database ``Session`` instance to live as
long as our web request does.

On the other hand we may want our ``Redis`` class instance - which is
thread-safe and uses connection pool to live for as long as the
application, regardless of the web request lifetime.

``injectpy`` has three lifetime types:

* ``transient``: default lifetime. It means that a new class instance
  is created every time (they are never re-used).
* ``singleton``: only a single instance will be created and every time
  an instance is requested we will re-use it.
* ``scoped``: only one instance is created per scope. You'll learn to
  manage scopes later in this chapter.

Specyfing lifetime
------------------

Specyfing lifetime is pretty easy: just use ``lifetime`` argument:

.. code-block:: python

    from injectpy import Kernel, Singleton, Scoped

    kernel = Kernel()

    kernel.bind(Flask, factory=app_factory, lifetime=Singleton)

``lifetime`` argument applies to a binding. This means that if you
set lifetime on a concrete class - only a single instance will be
created of that class, like above.

Let's consider a different example. When writing tests you may want to
bind some e-mail interface to an implementation which doesn't send out
real e-mails and allows you to inspect them:

.. code-block:: python

    kernel.bind(IEmailPort, to=InMemoryEmailAdapter, lifetime=Singleton)

    # create service
    service = kernel.get(RegistrationService)
    adapter = kernel.get(InMemoryEmailAdapter)
    # simulate registration
    service.register('john@example.com')
    # make sure that the e-mail was sent
    assert len(adapter.inbox) == 1

The above test **WILL FAIL**. The reason is that ``lifetime`` applies to
``IEmailPort``. So:

.. code-block:: python

    kernel.bind(IEmailPort, to=InMemoryEmailAdapter, lifetime=Singleton)

    inst1 = kernel.get(IEmailPort)
    inst2 = kernel.get(InMemoryEmailAdapter)
    
    assert inst1 is not inst2


To make sure that we get only one instance of ``InMemoryEmailAdapter``,
not ``IEmailPort`` we need to apply ``lifetime`` like this:

.. code-block:: python

    kernel.bind(IEmailPort, to=InMemoryEmailAdapter)
    kernel.bind(InMemoryEmailAdapter, lifetime=Singleton)

    inst1 = kernel.get(IEmailPort)
    inst2 = kernel.get(InMemoryEmailAdapter)

    assert inst1 is inst2


Controlling scope
-----------------

TBD
