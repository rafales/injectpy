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

import attr


@attr.dataclass(frozen=True)
class Binding:
    """
    Information about a single binding.
    """

    service: type
    instance: Optional[Any] = None
    to: Optional[Any] = None


T = TypeVar("T")


class Kernel:
    def __init__(self) -> None:
        self._bindings = DefaultDict[type, List[Binding]](list)

    def bind(self, service: Any, to: Any = None, instance: Any = None):
        """
        Configures a binding.
        """
        binding = Binding(service=service, to=to, instance=instance)
        self._bindings[service].append(binding)

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

        bound_to = binding.to or binding.service
        inspection = Inspection.inspect(bound_to)

        def _resolve_param(param: Parameter):
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
