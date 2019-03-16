import sys
import itertools
import threading
from typing import Any, List
import pytest
from injectpy import Kernel, Lifetime, BindingIsScoped
from tests.types import InMemoryFileSystem, IFileSystem


def test_transient_scoping() -> None:
    """
    Transient scoping is the most simple one. We always
    return new instance.
    """
    kernel = Kernel()
    # transient is the default lifetime
    kernel.bind(InMemoryFileSystem)

    inst1 = kernel.get(InMemoryFileSystem)
    inst2 = kernel.get(InMemoryFileSystem)

    assert isinstance(inst1, InMemoryFileSystem)
    assert isinstance(inst2, InMemoryFileSystem)
    # we always create new instance so those two should be different ones
    assert inst1 is not inst2


def test_singleton_scoping() -> None:
    """
    When instance is marked as a singleton - there should be only
    one instance per container.
    """
    kernel = Kernel()
    kernel.bind(InMemoryFileSystem, lifetime=Lifetime.singleton)

    inst1 = kernel.get(InMemoryFileSystem)
    inst2 = kernel.get(InMemoryFileSystem)

    assert inst1 is inst2


def test_singleton_from_transient() -> None:
    """
    When two transient classes have singleton as a dependency
    it should obviously be the same instance.
    """
    kernel = Kernel()

    class MyHandler:
        def __init__(self, fs: IFileSystem) -> None:
            self.fs = fs

    # note: singleton applies to "IFileSystem" here, not "InMemoryFileSystem"
    kernel.bind(IFileSystem, to=InMemoryFileSystem, lifetime=Lifetime.singleton)

    sing1 = kernel.get(IFileSystem)  # type: ignore
    inst1 = kernel.get(MyHandler)
    inst2 = kernel.get(MyHandler)

    assert inst1 is not inst2
    assert inst1.fs is inst2.fs is sing1  # singleton


def test_scoped_instances_are_not_shared() -> None:
    """
    When some instance is "Scoped":
    - it must be shared inside a single scope
    - it must NOT be shared between different scopes
    """
    kernel = Kernel()

    kernel.bind(InMemoryFileSystem, lifetime=Lifetime.scoped)
    inst1 = None
    inst2 = None

    with kernel.nested_scope() as scope:
        inst1 = scope.get(InMemoryFileSystem)
        another = scope.get(InMemoryFileSystem)
        assert inst1 is another

    with kernel.nested_scope() as scope:
        inst2 = scope.get(InMemoryFileSystem)
        another = scope.get(InMemoryFileSystem)
        assert inst2 is another

    assert inst1 is not inst2


def test_singleton_with_chained_bindings() -> None:
    """
    When a binding is a singleton then it must apply even if there
    is a binding chain.
    """
    kernel = Kernel()

    kernel.bind(InMemoryFileSystem, lifetime=Lifetime.singleton)
    kernel.bind(IFileSystem, to=InMemoryFileSystem)

    # because InMemoryFileSystem is a singleton there can be only one
    # instance of it, even if we request something through two different interfaces
    inst1 = kernel.get(InMemoryFileSystem)
    inst2 = kernel.get(IFileSystem)  # type: ignore

    assert inst1 is inst2


def test_chained_bindings_early_singleton() -> None:
    """
    On the other hand - if we set singleton on the interface itself then
    that's where it should be applied.
    """
    kernel = Kernel()

    kernel.bind(InMemoryFileSystem)
    kernel.bind(IFileSystem, to=InMemoryFileSystem, lifetime=Lifetime.singleton)

    inst1 = kernel.get(IFileSystem)  # type: ignore
    inst2 = kernel.get(InMemoryFileSystem)

    # only "IFileSystem" is a singleton, so requesting InMemoryFileSystem should
    # give us different instance.
    assert inst1 is not inst2


def test_scoped_with_chained_bindings() -> None:
    """
    When a binding is scoped then it must apply even if there
    is a binding chain.
    """
    kernel = Kernel()

    kernel.bind(InMemoryFileSystem, lifetime=Lifetime.scoped)
    kernel.bind(IFileSystem, to=InMemoryFileSystem)

    with kernel.nested_scope() as scope:
        # because InMemoryFileSystem is scoped there can be only one
        # instance of it, even if we request something through two
        # different interfaces
        inst1 = scope.get(InMemoryFileSystem)
        inst2 = scope.get(IFileSystem)  # type: ignore

        assert inst1 is inst2


def test_chained_bindings_early_scoped() -> None:
    """
    On the other hand - if we set scoped on the interface itself then
    that's where it should be applied.
    """
    kernel = Kernel()

    kernel.bind(InMemoryFileSystem)
    kernel.bind(IFileSystem, to=InMemoryFileSystem, lifetime=Lifetime.scoped)

    with kernel.nested_scope() as scope:
        inst1 = scope.get(IFileSystem)  # type: ignore
        inst2 = scope.get(InMemoryFileSystem)

        # only "IFileSystem" is a singleton, so requesting InMemoryFileSystem should
        # give us different instance.
        assert inst1 is not inst2


def test_getting_scoped_class_from_kernel_raises_error() -> None:
    """
    When you try to retrieve scoped class from kernel directly
    you should get an error.
    """
    kernel = Kernel()

    kernel.bind(InMemoryFileSystem, lifetime=Lifetime.scoped)

    with pytest.raises(BindingIsScoped):
        kernel.get(InMemoryFileSystem)


def test_singleton_scope_is_thread_safe(request: Any) -> None:
    """
    When using singleton scope we must ensure that concurrent access
    is safe between different threads.
    """
    kernel = Kernel()

    kernel.bind(InMemoryFileSystem, lifetime=Lifetime.singleton)
    instances: List[InMemoryFileSystem] = []
    NUM_THREADS = 5
    barrier = threading.Barrier(NUM_THREADS, timeout=1)

    # we need to set "switch interval" to something really low to
    # trigger this problem reliably.
    interval = sys.getswitchinterval()
    request.addfinalizer(lambda: sys.setswitchinterval(interval))
    sys.setswitchinterval(0.00000001)

    def worker() -> None:
        barrier.wait()
        inst = kernel.get(InMemoryFileSystem)
        instances.append(inst)

    threads = [threading.Thread(target=worker) for i in range(NUM_THREADS)]
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert len(instances) == NUM_THREADS
    print(instances)
    for inst in instances[1:]:
        assert instances[0] is inst
