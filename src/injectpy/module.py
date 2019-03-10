"""
Modular configuration for container.
"""
import inspect
from typing import TypeVar, Callable, Any, get_type_hints, Optional
import attr
from .types import AbstractModule, Binder


TFn = TypeVar("TFn", bound=Callable)
FACTORY_ATTRIB_NAME = "__injectpy__factory__"


@attr.dataclass()
class FactoryInfo:
    service: Any


def factory() -> Callable[[TFn], TFn]:
    """
    Marks method of a Module as a factory function.
    """

    def decorator(fn: TFn) -> TFn:
        info = FactoryInfo(service=get_returned_type(fn))
        setattr(fn, FACTORY_ATTRIB_NAME, info)
        return fn

    return decorator


def get_returned_type(cb: Callable) -> Any:
    hints = get_type_hints(cb)
    return_hint = hints.get("return", None)
    return return_hint


class Module(AbstractModule):
    def install_module(self, binder: Binder) -> None:
        for _, meth in inspect.getmembers(self, inspect.ismethod):
            info: Optional[FactoryInfo] = getattr(meth, FACTORY_ATTRIB_NAME, None)
            if info:
                binder.bind(info.service, factory=meth)

        self.configure(binder)

    def configure(self, binder: Binder) -> None:
        pass
