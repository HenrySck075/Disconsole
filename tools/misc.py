from collections.abc import Callable
from typing import Iterable, TypeVar

T = TypeVar("T")
def callable_partial(func: Callable[..., T], *args, **kwargs) -> Callable[..., T]:
    "partial that does not makes type checkers angry for the fact that partial is not Callable"
    def __inner__(*args2, **kwargs2):
        return func(*args, *args2, **kwargs, **kwargs2)
    return __inner__

def find(items: Iterable[T], candidate: Callable[[T],bool]) -> T:
    for i in items:
        if candidate(i): return i
    raise ValueError("No items in list passed the candidate")
