from injectpy import Kernel
from tests.types import (
    IFileSystem,
    ISimpleEventBus,
    LocalFileSystem,
    NoopEventBus,
    S3FileSystem,
)

# TODO: nice error when can't instantiate abstract class / protocol
# TODO: detect circular dependencies
# TODO: ensure that protocols work :)
# TODO: "when" for contextual binding


class TestKernel:
    def test_self_binding_without_arguments(self) -> None:
        """
        Simplest of all: class binds to itself and has no arguments.
        """

        class MyClass:
            pass

        kernel = Kernel()
        kernel.bind(MyClass)

        inst = kernel.get(MyClass)
        assert isinstance(inst, MyClass)

    def test_binding_to_other_class_without_arguments(self) -> None:
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

    def test_type_hint_injection_for_self_bound_class(self) -> None:
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

    def test_optional_injection_when_missing(self) -> None:
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

    def test_optional_injection_when_bound(self) -> None:
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

    def test_factory_function(self) -> None:
        """
        It's possible to pass a function which will create given instance.
        """
        kernel = Kernel()
        kernel.bind(IFileSystem, factory=lambda: S3FileSystem())

        inst = kernel.get(IFileSystem)  # type: ignore
        assert isinstance(inst, S3FileSystem)

    def test_long_binding_chain(self) -> None:
        """
        You can create a binding chain that will span a couple of bindings.
        """

        class IReadOnlyDb:
            pass

        class IDb(IReadOnlyDb):
            pass

        class Db(IDb):
            pass

        kernel = Kernel()
        kernel.bind(IReadOnlyDb, to=IDb)
        kernel.bind(IDb, to=Db)

        inst1 = kernel.get(IReadOnlyDb)
        inst2 = kernel.get(IDb)
        assert isinstance(inst1, Db)
        assert isinstance(inst2, Db)

    def test_rebind_changes_binding(self) -> None:
        """
        You can use rebind() to change existing binding.
        It's useful mainly for testing purposes.
        """
        kernel = Kernel()

        kernel.bind(IFileSystem, to=S3FileSystem)
        kernel.rebind(IFileSystem, to=LocalFileSystem)

        inst = kernel.get(IFileSystem)  # type: ignore
        assert isinstance(inst, LocalFileSystem)

    def test_rebind_doesnt_crash_if_binding_does_not_exist(self) -> None:
        """
        rebind() should not crash if binding doesn't already exist.
        """
        kernel = Kernel()

        kernel.rebind(IFileSystem, to=S3FileSystem)

        inst = kernel.get(IFileSystem)  # type: ignore
        assert isinstance(inst, S3FileSystem)
