import abc
import enum
from typing import Any, Callable


class Lifetime(enum.Enum):
    """
    Marks lifetime of an instance.
    """

    singleton = enum.auto()
    transient = enum.auto()
    scoped = enum.auto()


class Binder(abc.ABC):
    """
    Exposes interface for binding dependencies.
    """

    @abc.abstractmethod
    def bind(
        self,
        service: Any,
        *,
        to: Any = None,
        factory: Callable = None,
        instance: Any = None,
        lifetime: Lifetime = Lifetime.transient,
    ) -> None:
        raise NotImplementedError


class AbstractModule(abc.ABC):
    """
    Exposes interface for modules installable into container.
    """

    @abc.abstractmethod
    def install_module(self, binder: Binder) -> None:
        raise NotImplementedError
