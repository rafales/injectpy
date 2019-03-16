"""
Set of useful types for testing purposes.
"""
import abc
import attr
from typing import Dict, Any, List


class IFileSystem(abc.ABC):
    """
    Fake class for managing file system.
    """

    @abc.abstractmethod
    def exists(self, path: str) -> bool:
        raise NotImplementedError


class InMemoryFileSystem(IFileSystem):
    """
    A simple in-memory FS.
    """

    def __init__(self) -> None:
        self._contents: Dict[str, bytes] = {}

    def add(self, name: str, contents: bytes) -> None:
        self._contents[name] = contents

    def exists(self, path: str) -> bool:
        return path in self._contents


class LocalFileSystem(IFileSystem):
    def add(self, name: str, contents: bytes) -> None:
        raise NotImplementedError("This is just for tests, don't call")

    def exists(self, path: str) -> bool:
        raise NotImplementedError("This is just for tests, don't call")


class S3FileSystem(IFileSystem):
    def add(self, name: str, contents: bytes) -> None:
        raise NotImplementedError("This is just for tests, don't call")

    def exists(self, path: str) -> bool:
        raise NotImplementedError("This is just for tests, don't call")


@attr.dataclass()
class HttpRequest:
    """
    Fake http request class.
    """

    path: str
    domain: str = "example.com"
    secure: bool = True
    post: Dict[str, str] = attr.ib(factory=dict, converter=dict)


class HttpHandler(abc.ABC):
    """
    A fake class for handling http requests.
    """

    @abc.abstractmethod
    def handle(self, request: HttpRequest) -> Any:
        raise NotImplementedError


class ISimpleEventBus(abc.ABC):
    """
    A fake class for sending events.
    """

    @abc.abstractclassmethod
    def emit(self, name: str, params: Dict[str, Any]) -> None:
        raise NotImplementedError


class NoopEventBus(ISimpleEventBus):
    def emit(self, name: str, params: Dict[str, Any]) -> None:
        pass


class IWebRouter(abc.ABC):
    """
    A fake class for routing web requests :)
    """

    @abc.abstractmethod
    def add_route(self, cls: type) -> None:
        raise NotImplementedError


class WebRouter(IWebRouter):
    def __init__(self) -> None:
        self.routes: List[type] = []

    def add_route(self, cls: type) -> None:
        self.routes.append(cls)
