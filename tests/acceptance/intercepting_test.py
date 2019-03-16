import pytest

from injectpy import Kernel, Module, intercept
from tests.types import IWebRouter, WebRouter


def test_interceptors_allow_you_to_modify_instances() -> None:
    """
    Interceptors allow us to modify instances of given service
    before it gets returned.
    """

    class MyRoute:
        pass

    def handler(router: WebRouter) -> None:
        router.add_route(MyRoute)

    kernel = Kernel()
    kernel.intercept(WebRouter, handler=handler)
    inst = kernel.get(WebRouter)

    assert inst.routes == [MyRoute]


def test_interceptors_can_be_chained() -> None:
    """
    Interceptors must chain.
    """

    class MyRoute1:
        pass

    class MyRoute2:
        pass

    def handler1(router: WebRouter) -> None:
        router.add_route(MyRoute1)

    def handler2(router: IWebRouter) -> None:
        router.add_route(MyRoute2)

    kernel = Kernel()
    kernel.bind(IWebRouter, to=WebRouter)
    kernel.intercept(WebRouter, handler=handler1)
    kernel.intercept(IWebRouter, handler=handler2)  # type: ignore

    inst = kernel.get(IWebRouter)  # type: ignore

    assert isinstance(inst, WebRouter)
    assert inst.routes == [MyRoute1, MyRoute2]


def test_module_registers_interceptors() -> None:
    """
    Module allows for registering interceptors.
    """

    class MyRoute1:
        pass

    class MyModule(Module):
        @intercept()
        def init_router(self, router: WebRouter) -> None:
            router.add_route(MyRoute1)

    kernel = Kernel()
    kernel.install(MyModule())
    inst = kernel.get(WebRouter)

    assert isinstance(inst, WebRouter)
    assert inst.routes == [MyRoute1]


def test_error_when_first_parameter_is_untyped() -> None:
    """
    An exception must be raised if first parameter is not typed properly.
    """
    with pytest.raises(RuntimeError) as info:

        class MyModule(Module):
            @intercept()
            def my_interceptor(self, something):  # type: ignore
                pass

    assert str(info.value) == "'my_interceptor' has untyped first argument 'something'"


def test_error_when_cant_locale_first_parameter() -> None:
    """
    If method doesn't have first param then we need to raise an error.
    """

    with pytest.raises(RuntimeError) as info:

        class MyModule(Module):
            @intercept()  # type: ignore
            def my_interceptor(self) -> None:
                pass

    assert str(info.value) == "'my_interceptor' has no first positional argument"
