## NewType pattern ✅

Sometimes we want to inject different instances into different classes. One way to do this is to use `NewType`:

```python
from typing import NewType
from pathlib import PurePath, Path
from mylib import IFileSystem, S3FileSystem, LocalFileSystem
from injectpy import Kernel


NetworkedFileSystem = NewType('NetworkedFileSystem', IFileSystem)


class MyUploader:
    def __init__(self, input_fs: IFileSystem, output_fs: NetworkedFileSystem) -> None:
        self.input_fs = input_fs
        self.output_fs = output_fs

    def upload(self, in_path: PurePath, out_path: PurePath) -> None:
        with self.input_fs.open(in_path) as fp:
            self.output_fs.save(out_path, fp)


container = Kernel()
container.bind(IFileSystem, instance=LocalFileSystem("./files/"))
container.bind(NetworkedFileSystem, instance=S3FileSystem())  # reads AWS_* env variables

uploader = container.get(MyUploader)
assert isinstance(uploader.input_fs, LocalFileSystem)
assert isinstance(uploader.output_fs, NetworkedFileSystem)
```

## Module pattern ✅

Instead of binding everything to a container - we can use a module - a separated piece of bindings:

```python
from pathlib import Path
from injectpy import Module, Kernel, Binder, factory


class MyModule(Module):
    @factory()
    def create_filesystem(self, settings: Settings) -> IFileSystem:
        return LocalFileSystem(path=Path(settings['MEDIA_DIR']).resolve())

    def configure(self, binder: Binder) -> None:
        binder.bind(ISimpleEventBus, to=RedisEventBus)

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

Note: while guice supports weird patterns for doing this - we want
only to support list of bindings.

If you need a more advanced pattern you can use factories and/or combine
them with interceptors.

## Scopes ✅

Instead of taking Ninject's approach to scopes we follow what AutoFac
or .NET Core DI do. We have three kinds of lifetimes:

- Singleton - only a single instance for the whole kernel
- Scoped - instances live as long as a scope does
- Transient - new instance is created every time

Of those three two are pretty easy: singleton and transient. `Scoped` needs
more explaining. Basically we do something like this:

```python

with kernel.new_scope() as scope:
    db_session = scope.get(Session)
    db_session.add(User(name="John"))
    db_session.commit()

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

## Interceptors / activation actions ✅

Sometimes we need to modify the class that container returns. A fine example would be a `WebRouter` class which needs to know about other classes that acutally implement routes. With interceptors you could plug into class creation process and modify it before it gets injected into the class like this:

```python
from injectpy import Module, intercept

class MyModule(Module):
    @intercept(WebRouter)
    def init_web_router(self, router: WebRouter) -> None:
        router.add(PostsController)
        router.add(PostsAdminController, prefix='/admin')


# somewhere else
kernel = Kernel()
kernel.install(WebModule)
kernel.install(MyModule)

# router has all routes registered through interceptors
router = kernel.get(WebRouter)
```

## Passing kwargs

When you bind a class it may be useful to set arguments for a concrete class like this:

```python

kernel.bind(IFileSystem, to=LocalFileSystem, kwargs={'base_path': '/some/path'})
```

## Generics

TBD

## Async

TBD

## Nesting scopes

TBD
