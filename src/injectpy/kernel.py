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
from .utils import strip_optional
from .reflection import Inspection, Parameter
from .types import Binder, AbstractModule

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


T = TypeVar("T")


class Kernel(Binder):
    def __init__(self) -> None:
        self._bindings: DefaultDict[type, List[Binding]] = DefaultDict(list)

    def bind(
        self,
        service: Any,
        *,
        to: Any = None,
        factory: Callable = None,
        instance: Any = None
    ) -> None:
        """
        Configures a binding.
        """
        binding = Binding(service=service, to=to, instance=instance, factory=factory)
        self._bindings[service].append(binding)

    def install(self, module: AbstractModule) -> None:
        """
        Installs module into the kernel.
        """
        module.install_module(self)

    def get(self, interface: Type[T]) -> T:
        """
        Returns instance for given interface.
        """
        try:
            binding = self._bindings[interface][-1]
        except IndexError:
            binding = Binding(interface)

        if binding.instance:
            return binding.instance

        bound_to = binding.to or binding.factory or binding.service
        inspection = Inspection.inspect(bound_to)

        def _resolve_param(param: Parameter) -> Any:
            assert param.hint is not None
            if param.has_default and param.hint not in self._bindings:
                return None

            return self.get(param.hint)

        arguments = {
            param.name: _resolve_param(param)
            for param in inspection.parameters
            if param.hint is not None
        }

        return bound_to(**arguments)
