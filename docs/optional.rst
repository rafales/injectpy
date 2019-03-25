Pattern: optional injection
===========================

When building reusable components sometimes we may want to make
dependences optional.

Let's imagine that we are building a class which handles user authentication
that we will re-use between different projects:

.. code-block:: python

    class AuthenticationService:
        def __init__(
            self,
            web_session: IWebSession,
            security_ctx: ISecurityCtx,
            event_bus: IEventBus,
        ) -> None:
        
            self.web_session = web_session
            self.security_ctx = security_ctx
            self.event_bus = event_bus

        def logout(self) -> None:
            """
            Logs out current user.
            """
            user_id = self.security_ctx.user.id
            self.web_session.flush()
            self.event_bus.emit('logged_out', { 'user_id': user_id })
        
        # ... more code

In some of them we are using Kafka or other event stream broker (Kinesis, Redis,
maybe even RabbitMQ) to publish different events from the system for
analytics (``IEventBus``).

But in some of our projects we don't need such functionality. Does this mean
that we must create two separate ``AuthenticationService`` classes? No.

There are two ways to handle this situation.

Optional Injection
------------------

First one is to use optional injection. We simply make the ``event_bus``
optional and check if it's not ``None`` before calling it:

.. code-block:: python
    :emphasize-lines: 6,19-20

    class AuthenticationService:
        def __init__(
            self,
            web_session: IWebSession,
            security_ctx: ISecurityCtx,
            event_bus: Optional[IEventBus] = None,
        ) -> None:
        
            self.web_session = web_session
            self.security_ctx = security_ctx
            self.event_bus = event_bus

        def logout(self) -> None:
            """
            Logs out current user.
            """
            user_id = self.security_ctx.user.id
            self.web_session.flush()
            if self.event_bus:
                self.event_bus.emit('logged_out', { 'user_id': user_id })
        
        # ... more code


If ``injectpy`` won't be able to find a binding for ``IEventBus`` it will
use ``None`` value instead of rising an error.


Null Object Pattern
-------------------

Another way to handle this situation is to use "Null Object Pattern" - basically
an implementation that does nothing:


.. code-block:: python

    class NullEventBus(IEventBus):
        def emit(self, event_name: str, params: Dict[str, Any]) -> None:
            # null implementation, do nothing
            pass


Now, depending on the project you may bind ``IEventBus`` either to real
implementation like ``RedisEventBus`` or null one which does nothing:

.. code-block:: python

    kernel = Kernel()
    # we use redis implementation in projects which need to publish events
    kernel.bind(IEventBus, to=RedisEventBus)
    # we use null implementation if we don't want to publish anything
    kernel.bind(IEventBus, to=NullEventBus)


.. note::

    Both patterns will be equally good choices in most situations. You should
    probably go with "Null Object Pattern" when possible though, as it doesn't
    add any additional logic to the client class.
