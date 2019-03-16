"""
Checks using container with attrs library.
"""
import abc
from typing import Any, Optional

import attr
import pytest

from injectpy import Kernel
from tests.types import (
    HttpHandler,
    HttpRequest,
    IFileSystem,
    InMemoryFileSystem,
    ISimpleEventBus,
    NoopEventBus,
)


def test_discovers_dependencies_correctly() -> None:
    """
    Using attrs library instead of creating constructor manually is
    a really useful pattern - you just place type hints on class and
    you don't have to create your own constructor.
    """

    @attr.dataclass()
    class MyHandler:
        fs: IFileSystem
        request: HttpRequest

    kernel = Kernel()
    kernel.bind(IFileSystem, to=InMemoryFileSystem)
    kernel.bind(HttpRequest, instance=HttpRequest("/test"))
    handler = kernel.get(MyHandler)

    assert isinstance(handler, MyHandler)
    assert isinstance(handler.fs, InMemoryFileSystem)
    assert handler.request == HttpRequest("/test")


def test_works_with_abc() -> None:
    """
    While using attrs classes we still must be able to implement ABCs.

    Otherwise this would be kinda useless.
    """

    @attr.dataclass()
    class CheckFileExists(HttpHandler):
        fs: IFileSystem

        def handle(self, request: HttpRequest) -> Any:
            file_name = request.post["name"]
            return {"exists": self.fs.exists(file_name)}

    kernel = Kernel()
    kernel.bind(IFileSystem, to=InMemoryFileSystem)
    handler = kernel.get(CheckFileExists)

    assert isinstance(handler, CheckFileExists)
    assert isinstance(handler.fs, InMemoryFileSystem)


def test_optional_injection() -> None:
    """
    Our container has a feature called "optional injection" where
    you can provide a default value if injection is not known to the container.
    """

    @attr.dataclass()
    class UpdateProfilePic:
        fs: IFileSystem
        # by providing default we make it possible for the binding
        # to be missing.
        event_bus: Optional[ISimpleEventBus] = None

    kernel = Kernel()
    kernel.bind(IFileSystem, to=InMemoryFileSystem)

    handler = kernel.get(UpdateProfilePic)
    assert isinstance(handler.fs, InMemoryFileSystem)
    assert handler.event_bus is None


def test_inheritance() -> None:
    """
    One interesting thing about attrs is how inheritance works.

    This makes handling DI for inheriting classes a breeze.
    """

    @attr.dataclass()
    class BaseHandler:
        request: HttpRequest

    @attr.dataclass()
    class MyHandler(BaseHandler):
        fs: IFileSystem

    kernel = Kernel()
    kernel.bind(IFileSystem, to=InMemoryFileSystem)
    kernel.bind(HttpRequest, instance=HttpRequest("/test"))

    handler = kernel.get(MyHandler)
    assert isinstance(handler, MyHandler)
    assert isinstance(handler.fs, InMemoryFileSystem)
    assert handler.request == HttpRequest("/test")
