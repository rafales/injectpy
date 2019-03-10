## NewType pattern

Sometimes we want to inject different instances into different classes. One way to do this is to use `NewType`:

```python
from typing import NewType
from pathlib import PurePath, Path
from mylib import IFileSystem, S3FileSystem, LocalFileSystem
from injectpy import Container


NetworkedFileSystem = NewType('NetworkedFileSystem', IFileSystem)


class MyUploader:
    def __init__(self, input_fs: IFileSystem, output_fs: NetworkedFileSystem) -> None:
        self.input_fs = input_fs
        self.output_fs = output_fs

    def upload(self, in_path: PurePath, out_path: PurePath) -> None:
        with self.input_fs.open(in_path) as fp:
            self.output_fs.save(out_path, fp)


container = Container()
container.bind(IFileSystem, to=LocalFileSystem("./files/"))
container.bind(NetworkedFileSystem, to=S3FileSystem())  # reads AWS_* env variables

uploader = container.get(MyUploader)
assert isinstance(uploader.input_fs, LocalFileSystem)
assert isinstance(uploader.output_fs, NetworkedFileSystem)
```

## Module pattern

Instead of binding everything to a container - we can use a module - a separated piece of bindings:

```python
from injectpy import Module, factory, Singleton

... TODO finish me
```

## Contextual bindings

Sometimes we want given binding to be used only in a certain context. We can use `when` parameter to do that:

```python
import uuid
from pathlib import PurePath
from mylib import IFileSystem, S3FileSystem


class UploadHandler:
    def __init__(self, fs: IFileSystem) -> None:
        self.fs = fs

    def handle(self, req: Request):
        file_name = PurePath('uploads', str(uuid.uuid4()))
        self.fs.save(file_name, req.files['file'])
        return {'ok': True}


# will use S3FileSystem in place of IFileSystem but only for UploadHandler class
container.bind(IFileSystem, to=S3FileSystem, when=ctx: ctx.cls is UploadHandler)
```

## Tagging pattern

I don't think we should include this by default, as it causes code to know
about the container but it's easily implementable:

```python

from mylib import tag, when_tag, IFileSystem, S3FileSystem


TAG_NETWORKED_FS = object()

# TODO: also make it possible to tag the class itself, it will
# be useful with attrs/dataclass pattern.

class UploadHandler:
    @tag('fs', TAG_NETWORKED_FS)
    def __init__(self, fs: IFileSystem) -> None:
        self.fs = fs

    def handle(self, req: Request):
        file_name = PurePath('uploads', str(uuid.uuid4()))
        self.fs.save(file_name, req.files['file'])
        return {'ok': True}


container.bind(IFileSystem, to=S3FileSystem, when=when_tag(TAG_NETWORKED_FS))
```

## Multi-binding

Multi-binding is an useful pattern for creating plugin systems. Let's consider:

```python
import abc


# Plugin's interface
class HttpMiddlewarePlugin(abc.ABC):
    @abc.abstractmethod
    def next(self, req: Request, get_response: Callable[[], Response]) -> Response:
        raise NotImplementedError


# First plugin which bans tor users, note that it can accept dependencies
# in __init__ just as any class would do
class BanTorUsers(HttpMiddlewarePlugin):
    def __init__(self, detector: TorDetector) -> None:
        self.detector = detector

    def next(self, req: Request, get_response: Callable[[], Response]) -> Response:
        if self.detector.is_tor_ip(req.ip_address):
            return self.reject()

        return get_response()

    def reject(self) -> Response:
        ...


# Second plugin which disables cache
class DisableCache(HttpMiddlewarePlugin):
    def next(self, req: Request, get_response: Callable[[], Response]) -> Response:
        resp = get_response()
        resp.headers['Cache-Control'] = 'no-cache'
        return resp


# Now how we use this: all you need to do is to accept list of instances:
class HttpHandler:
    def __init__(self, plugins: List[HttpMiddlewarePlugin]) -> None:
        self.plugins = plugins

    def _handle_request(self, req: Request) -> Response:
        # handles the request after middleware
        ...

    def handle(self, req: Request) -> Response:
        get_response = partial(self._handle_request, req)

        for plugin in reversed(self.plugins):
            get_response = partial(plugin.next, req, get_response)

        return get_response()


container.multibind(HttpMiddlewarePlugin, to=DisableCache)
container.multibind(HttpMiddlewarePlugin, to=BanTorUsers)

handler = container.get(HttpHandler)
resp = handler.handle(FakeRequest('/'))
```

## Using attrs / dataclasses

If you don't like injecting dependencies through `__init__` method due to some boilerplate you can use `attrs` or `dataclasses` library. You can define your classes using class annotations while the library will create proper constructor for you:

```python
import abc
import attr


class HttpHandler(abc.ABC):
    @abc.abstractmethod
    def handle(self, req: Request):
        raise NotImplementedError


@attr.dataclass()
class UploadHandler(HttpHandler):  # works with abc's
    fs: IFileSystem

    def handle(self, req: Request):
        file_name = PurePath('uploads', str(uuid.uuid4()))
        self.fs.save(file_name, req.files['file'])
        return {'ok': True}
```

## Optional injection

Sometimes you wan't to handle situation where some dependency is only optional. In those situations you can set a default for an argument:

```python
import abc


class IEventBus(abc.ABC):
    def emit(self, name: str, params: Dict[str, Any]) -> None:
        raise NotImplementedError


class UpdateProfile(HttpHandler):
    def __init__(self, event_bus: IEventBus = None) -> None:
        self.event_bus = event_bus

    def handle(self, req: Request):
        # ...
        if self.event_bus is not None:
            self.event_bus.emit('profile-updated', {'...': '...'})


## when we comment this line out - container will omit 'event_bus' when constructing UpdateProfile instance.
# container.bind(IEventBus, MyEventBus, scope=Singleton)
```

## Activation actions

## Scopes

## Disposing / cleaning up

Some instances must be cleaned up. C# has a concept of "disposing" which works great with ninject. Python has different mechanism - `with` (or `__enter__` / `__exit__`). But that would not work as equally good.

Idea: just add `dispose` param:

```python

# Option 1:
container.bind(Session, to=make_session, dispose=lambda session: session.close())

# Option 2:
@contextlib.contextmanager
def make_session():
    session = Session()
    try:
        yield session
    finally:
        session.close()

container.bind(Session, to=make_session, dispose=True)
```

## Union bindings

What if we could accept two different interfaces, depending on what's available
and first?

```python

class MyCommand:
    def __init__(self, server: Union[HttpServer, GrpcServer]) -> None:
        self.server = server

    def run(self) -> None:
        self.server.start()

        at = f"{self.server.host}:{self.server.port}"
        if isinstance(self.server, HttpServer):
            at = f"http://{at}"

        print(f"Server is running at {at}")

```

## Handling missing bindings
