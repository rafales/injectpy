import abc
import inspect
import threading
import contextlib
from typing import (
    Any,
    Callable,
    DefaultDict,
    Dict,
    List,
    NewType,
    Optional,
    Type,
    TypeVar,
    Union,
    Tuple,
    get_type_hints,
)
from collections import OrderedDict
from .utils import strip_optional
from .reflection import Inspection, Parameter
from .types import Binder, AbstractModule, Lifetime
from .exceptions import BindingIsScoped

import attr


@attr.dataclass(frozen=True)
class Binding:
    """
    Information about a single binding.
    """

    service: type
    instance: Optional[Any] = None
    to: Optional[Any] = None
    factory: Optional[Callable] = None
    lifetime: Lifetime = Lifetime.transient


T = TypeVar("T")


class Scope:
    def __init__(self, kernel: "Kernel") -> None:
        self._kernel = kernel
        self._instances: Dict[Any, Any] = OrderedDict()

    def __enter__(self) -> "Scope":
        return self

    def __exit__(
        self, exc_type: Type[BaseException], exc_val: BaseException, exc_tb: Any
    ) -> bool:
        self._instances = OrderedDict()
        return False

    def get(self, interface: Type[T]) -> T:
        return self._kernel._get(interface, scope=self)


class Kernel(Binder):
    def __init__(self) -> None:
        self._bindings: DefaultDict[type, List[Binding]] = DefaultDict(list)
        self._singleton: Dict[Any, Any] = OrderedDict()
        self._singleton_lock = threading.RLock()

    def bind(
        self,
        service: Any,
        *,
        to: Any = None,
        factory: Callable = None,
        instance: Any = None,
        lifetime: Lifetime = Lifetime.transient,
    ) -> None:
        """
        Configures a binding.
        """
        binding = Binding(
            service=service,
            to=to,
            instance=instance,
            factory=factory,
            lifetime=lifetime,
        )
        self._bindings[service].append(binding)

    def install(self, module: AbstractModule) -> None:
        """
        Installs module into the kernel.
        """
        module.install_module(self)

    def nested_scope(self) -> Scope:
        """
        Returns a new scope for scoped bindings.
        """
        return Scope(kernel=self)

    def get(self, interface: Type[T]) -> T:
        """
        Returns instance for given interface.
        """
        return self._get(interface)

    def _get(self, interface: Type[T], scope: Scope = None) -> T:
        try:
            binding = self._bindings[interface][-1]
        except IndexError:
            binding = Binding(interface)

        if binding.instance:
            return binding.instance

        lock: Any = contextlib.nullcontext()
        cache: Optional[Dict[Any, Any]] = None

        if binding.lifetime == Lifetime.singleton:
            lock = self._singleton_lock
            cache = self._singleton
        elif binding.lifetime == Lifetime.scoped:
            if scope is None:
                # attempted to use scoped binding but no scope is active
                raise BindingIsScoped()

            cache = scope._instances

        if cache and binding.service in cache:
            return cache[binding.service]

        with lock:
            # double lock pattern for singleton scope
            if cache and binding.service in cache:
                return cache[binding.service]

            if binding.to:
                instance = self._get(binding.to, scope=scope)
            else:
                bound_to = binding.factory or binding.service
                inspection = Inspection.inspect(bound_to)

                def _resolve_param(param: Parameter) -> Any:
                    assert param.hint is not None
                    if param.has_default and param.hint not in self._bindings:
                        return None

                    return self._get(param.hint, scope=scope)

                arguments = {
                    param.name: _resolve_param(param)
                    for param in inspection.parameters
                    if param.hint is not None
                }

                instance = bound_to(**arguments)

            if cache is not None:
                cache[binding.service] = instance

        return instance
