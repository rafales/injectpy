from injectpy import Kernel
from tests.types import ISimpleEventBus, NoopEventBus

# TODO: nice error when can't instantiate abstract class / protocol
# TODO: detect circular dependencies
# TODO: ensure that protocols work :)
# TODO: add factory function support
# TODO: "when" for contextual binding
# TODO: scopes


class TestKernel:
    def test_self_binding_without_arguments(self):
        """
        Simplest of all: class binds to itself and has no arguments.
        """

        class MyClass:
            pass

        kernel = Kernel()
        kernel.bind(MyClass)

        inst = kernel.get(MyClass)
        assert isinstance(inst, MyClass)

    def test_binding_to_other_class_without_arguments(self):
        """
        You can bind an interface to a different class.
        """

        class MyInterface:
            pass

        class MyImpl(MyInterface):
            pass

        kernel = Kernel()
        kernel.bind(MyInterface, to=MyImpl)

        inst = kernel.get(MyInterface)
        assert isinstance(inst, MyImpl)

    def test_type_hint_injection_for_self_bound_class(self):
        """
        You can use type hints to specify other classes your class
        depends on.
        """

        class Database:
            pass

        class MyService:
            def __init__(self, db: Database) -> None:
                self.db = db

        kernel = Kernel()
        kernel.bind(Database)
        kernel.bind(MyService)

        inst = kernel.get(MyService)
        assert isinstance(inst, MyService)
        assert isinstance(inst.db, Database)

    def test_optional_injection_when_missing(self):
        """
        You can use a default value to make an injection optional.

        When done - if an explicit binding won't be found container will
        omit that argument.

        In this case we test situation where dependency is abstract.
        """

        class MyHandler:
            def __init__(self, bus: ISimpleEventBus = None) -> None:
                self.bus = bus

        kernel = Kernel()
        inst = kernel.get(MyHandler)

        assert isinstance(inst, MyHandler)
        assert inst.bus is None

    def test_optional_injection_when_bound(self):
        """
        When dependency has a default value but it's present in
        container - fill it as usual.
        """

        class MyHandler:
            def __init__(self, bus: ISimpleEventBus = None) -> None:
                self.bus = bus

        kernel = Kernel()
        kernel.bind(ISimpleEventBus, to=NoopEventBus)

        inst = kernel.get(MyHandler)
        assert isinstance(inst, MyHandler)
        assert isinstance(inst.bus, NoopEventBus)
