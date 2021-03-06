"""
Modular configuration for container.
"""
import inspect
from typing import Any, Callable, TypeVar, Union, get_type_hints

import attr

from .reflection import Inspection
from .types import AbstractModule, Binder, Lifetime

T = TypeVar("T")
TFn = TypeVar("TFn", bound=Callable)
INFO_ATTRIB_NAME = "__injectpy__info__"


@attr.dataclass()
class FactoryInfo:
    service: Any
    lifetime: Lifetime


@attr.dataclass()
class InterceptInfo:
    service: Any


def factory(*, lifetime: Lifetime = Lifetime.transient) -> Callable[[TFn], TFn]:
    """
    Marks method of a Module as a factory function.
    """

    def decorator(fn: TFn) -> TFn:
        info = FactoryInfo(service=get_returned_type(fn), lifetime=lifetime)
        setattr(fn, INFO_ATTRIB_NAME, info)
        return fn

    return decorator


TInterceptHandler = TypeVar("TInterceptHandler", bound=Callable[[Any, Any], None])


def intercept() -> Callable[[TInterceptHandler], TInterceptHandler]:
    def decorator(fn: Any) -> Any:
        info = InterceptInfo(service=get_first_hint(fn))
        setattr(fn, INFO_ATTRIB_NAME, info)
        return fn

    return decorator


def get_returned_type(cb: Callable) -> Any:
    hints = get_type_hints(cb)
    return_hint = hints.get("return", None)
    return return_hint


def get_first_hint(cb: Callable) -> Any:
    inspection = Inspection.inspect(cb)

    positional = [param for param in inspection.parameters if param.is_positional()]

    try:
        # we omit "self"
        param = positional[1]
        if param.hint is None:
            raise RuntimeError(
                f"'{cb.__name__}' has untyped first argument '{param.name}'"
            )
        return param.hint
    except IndexError:
        raise RuntimeError(f"'{cb.__name__}' has no first positional argument")


class Module(AbstractModule):
    def install_module(self, binder: Binder) -> None:
        info: Union[FactoryInfo, InterceptInfo, None]
        for _, meth in inspect.getmembers(self, inspect.ismethod):
            info = getattr(meth, INFO_ATTRIB_NAME, None)
            if isinstance(info, FactoryInfo):
                binder.bind(info.service, factory=meth, lifetime=info.lifetime)
            elif isinstance(info, InterceptInfo):
                binder.intercept(info.service, handler=meth)

        self.configure(binder)

    def configure(self, binder: Binder) -> None:
        pass
