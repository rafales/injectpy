from typing import Any, Tuple, Union


def strip_optional(hint: Any) -> Tuple[bool, Any]:
    """
    Strips Optional[] from type hint.

    :returns: tuple with bool (indicating if hint was optional) and new hint
    """
    origin = getattr(hint, "__origin__", None)
    if origin is not Union:
        return hint, False

    args = hint.__args__
    none_type: Any = type(None)
    if none_type not in args:
        return hint, False

    new_args = tuple(filter(lambda t: t is not none_type, args))
    return Union[new_args], True
