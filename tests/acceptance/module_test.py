from injectpy import Binder, Kernel, Module, factory, Singleton
from tests.types import IFileSystem, InMemoryFileSystem, S3FileSystem


def test_factory_decorator() -> None:
    """
    Modules have a feature for easily defining
    factory functions: @factory() decorator.
    """

    class MyModule(Module):
        @factory()
        def my_filesystem(self) -> IFileSystem:
            return S3FileSystem()

    kernel = Kernel()
    kernel.install(MyModule())
    inst = kernel.get(IFileSystem)  # type: ignore
    inst2 = kernel.get(IFileSystem)  # type: ignore

    assert isinstance(inst, S3FileSystem)
    assert inst2 is not inst  # transient lifetime by default


def test_factory_customizing_lifetime() -> None:
    """
    @factory() decorator allows for customization of
    a lifetime of the binding.
    """

    class MyModule(Module):
        @factory(lifetime=Singleton)
        def my_filesystem(self) -> IFileSystem:
            return S3FileSystem()

    kernel = Kernel()
    kernel.install(MyModule())
    inst = kernel.get(IFileSystem)  # type: ignore
    inst2 = kernel.get(IFileSystem)  # type: ignore

    assert isinstance(inst, S3FileSystem)
    # we changed scope to singleton, so we should get the same instance
    assert inst2 is inst


def test_configure_fn() -> None:
    """
    Modules can also override configure() function
    to add any bindings.
    """

    class MyModule(Module):
        def configure(self, binder: Binder) -> None:
            binder.bind(IFileSystem, to=InMemoryFileSystem)

    kernel = Kernel()
    kernel.install(MyModule())

    inst = kernel.get(IFileSystem)  # type: ignore
    assert isinstance(inst, InMemoryFileSystem)
