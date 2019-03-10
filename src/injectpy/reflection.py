import inspect
from typing import Any, Dict, List, Optional, get_type_hints

import attr

from .utils import strip_optional


@attr.dataclass(frozen=True)
class Parameter:
    """
    Information about single parameter.
    """

    #: name of the parameter
    name: str
    #: if the parameter has a default value set
    has_default: bool
    #: resolved type hint (with Optional[] removed)
    hint: Optional[Any]
    #: if it was an union of Something and None.
    is_optional: bool

    @staticmethod
    def create(param: inspect.Parameter, hints: Dict[str, Any]) -> "Parameter":
        hint = hints.get(param.name, None)
        is_optional = False

        if hint is not None:
            hint, is_optional = strip_optional(hint)

        return Parameter(
            name=param.name,
            has_default=param.default is not inspect.Parameter.empty,
            hint=hint,
            is_optional=is_optional,
        )


@attr.dataclass(frozen=True)
class Inspection:
    obj: Any
    parameters: List[Parameter]

    @staticmethod
    def inspect(obj: Any) -> "Inspection":
        if inspect.isclass(obj):
            hints = get_type_hints(obj.__init__)
            sig = inspect.signature(obj)

            return Inspection(
                obj,
                parameters=[
                    Parameter.create(param, hints) for param in sig.parameters.values()
                ],
            )

        raise NotImplementedError(f"{obj!r} is not recognized by Kernel yet.")
