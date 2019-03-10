from injectpy import Kernel, Module, Binder, factory
from tests.types import IFileSystem, S3FileSystem, InMemoryFileSystem


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
    assert isinstance(inst, S3FileSystem)


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
