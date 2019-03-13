import abc
import inspect
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
    def __init__(self, parent: Optional["Scope"], kernel: "Kernel") -> None:
        self._parent = parent
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
        self._singleton = Scope(parent=None, kernel=self)

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
        return Scope(parent=self._singleton, kernel=self)

    def get(self, interface: Type[T]) -> T:
        """
        Returns instance for given interface.
        """
        return self._get(interface, scope=self._singleton)

    def _get(self, interface: Type[T], scope: Scope) -> T:
        try:
            binding = self._bindings[interface][-1]
        except IndexError:
            binding = Binding(interface)

        if binding.instance:
            return binding.instance

        if binding.lifetime != Lifetime.transient:
            # try to find instance in scope
            _scope: Optional[Scope] = scope
            while _scope is not None:
                if binding.service in _scope._instances:
                    return _scope._instances[binding.service]

                _scope = _scope._parent

        if binding.to:
            instance = self._get(binding.to, scope=self._singleton)
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

        # if lifetime is not transient - then persist instance in proper scope
        if binding.lifetime != Lifetime.transient:
            target_scope = (
                self._singleton if binding.lifetime == Lifetime.singleton else scope
            )
            target_scope._instances[binding.service] = instance

        return instance
