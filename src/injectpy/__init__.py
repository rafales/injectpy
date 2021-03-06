from .exceptions import BindingIsScoped
from .kernel import Kernel
from .module import Module, factory, intercept
from .types import Binder, Lifetime


Singleton = Lifetime.singleton
Transient = Lifetime.transient
Scoped = Lifetime.scoped


# this is the public API, the rest of the package is internal
__all__ = [
    "Kernel",
    "Module",
    "factory",
    "intercept",
    "Binder",
    "Lifetime",
    "BindingIsScoped",
    "Singleton",
    "Transient",
    "Scoped",
]
