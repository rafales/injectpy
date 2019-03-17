Pattern: using `attrs` and `dataclasses`
========================================

`attrs <https://github.com/python-attrs/attrs>`_ and
`dataclasses <https://docs.python.org/3/library/dataclasses.html>`_ are two
libraries which make it easy to create classes without creating too much
boilerplate.

One of the things it can do is creating ``__init__`` functions based on
class' type hints.


.. note::

    `injectpy` doesn't do anything special to support `attrs` and `dataclasses`.
    They create ``__init__`` methods with proper type hints, so `injectpy`
    works with them out of the box.

Let's consider this example:

.. code-block:: python

    from myapp.lib import IFileSystem, IUserRepository, IEmailGateway

    class RegistrationService:
        def __init__(self, fs: IFileSystem, repo: IUserRepository, email: IEmailGateway) -> None:
            self.fs = fs
            self.repo = repo
            self.email = email
        
        def register(self, username: str, password: str) -> None:
            ...


That's a lot of boilerplate just to tell what dependencies we need. Instead
of that we can use `attrs` to create ``__init__`` for us:

.. code-block:: python

    import attr
    from myapp.lib import IFileSystem, IUserRepository, IEmailGateway

    @attr.s(auto_attribs=True)
    class RegistrationService:
        fs: IFileSystem
        repo: IUserRepository
        email: IEmailGateway

        def register(self, username: str, password: str) -> None:
            ...

Here's an example using `dataclasses` library:

.. code-block:: python

    from dataclasses import dataclass
    from myapp.lib import IFileSystem, IUserRepository, IEmailGateway

    @dataclass()
    class RegistrationService:
        fs: IFileSystem
        repo: IUserRepository
        email: IEmailGateway

        def register(self, username: str, password: str) -> None:
            ...

That way we don't have to create constructor but we get one that we can
use directly and with `injectpy`:

.. code-block:: python

    # fine to use directly:
    service = RegistrationService(
        fs=InMemoryFileSystem(),
        repo=InMemoryUserRepository(),
        email=InMemoryEmailAdapter(),
    )

    # you can also use it with kernel out of the box:
    inst = kernel.get(RegistrationService)


Inheritance
-----------

While composition is almost always preferred to inheritance - both `attrs`
and `dataclasses` handle inheritance in a way that makes it really easy
to use with `injectpy`:

.. code-block:: python

    from dataclasses import dataclass

    @dataclass()
    class BaseHandler:
        request: HttpRequest

    @dataclass()
    class MyHandler(BaseHandler):
        fs: IFileSystem
    
    # it's possible to use the constructor directly:
    my_handler = MyHandler(request=some_req, fs=InMemoryFileSystem())

    # it's also fine to use it with injectpy
    inst = kernel.get(MyHandler)
