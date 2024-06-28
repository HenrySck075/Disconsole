from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")
def callable_partial(func: Callable[..., T], *args, **kwargs) -> Callable[..., T]:
    "partial that does not makes type checkers angry for the fact that partial is not Callable"
    def __inner__(*args2, **kwargs2):
        return func(*args, *args2, **kwargs, **kwargs2)
    return __inner__
