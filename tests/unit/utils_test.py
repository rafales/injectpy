from typing import List, Optional, Union

from injectpy.utils import strip_optional


class TestStripOptional:
    def test_not_union(self) -> None:
        assert strip_optional(int) == (int, False)
        assert strip_optional(List[int]) == (List[int], False)

    def test_union_without_none(self) -> None:
        assert strip_optional(Union[str, int]) == (Union[str, int], False)
        assert strip_optional(Union[str]) == (Union[str], False)

    def test_union_with_optional(self) -> None:
        assert strip_optional(Optional[Union[int, str]]) == (Union[int, str], True)
        assert strip_optional(Union[None, bool, str]) == (Union[bool, str], True)
