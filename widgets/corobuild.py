"""
NOTICE THE DIFFERENCES:

- CoroutineWidget: Build based on the result of the coroutine 
- AsyncWidget: Makes `compose` async
"""

import asyncio
from collections.abc import AsyncGenerator, Callable, Coroutine
from enum import Enum
from typing import Any, Generic, Optional, TypeVar
import traceback
from textual.app import ComposeResult
from textual.containers import Container
from textual.widget import Widget
from textual.widgets import Static

class CoroState(Enum):
    Waiting = 0
    Fulfilled = 1
    Rejected = 2

T = TypeVar("T")
class CoroutineWidget(Widget,Generic[T]):
    def __init__(self, coro: Coroutine[Any, Any, T], name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.result = None
        self._coro_task=asyncio.create_task(coro)
        self._coro_task.add_done_callback(self.cb)

    def cb(self,task:asyncio.Task[T]):
        dontbesilly = task.exception()
        if dontbesilly != None:
            self.result = self.compose_rejected(dontbesilly)
        if task.done():
            self.result = self.compose_fulfilled(task.result())
        asyncio.ensure_future(self.recompose(),loop=asyncio.get_event_loop())

    def compose_fulfilled(self,result: T) -> ComposeResult:
        yield Widget()
    def compose_rejected(self,exception:BaseException) -> ComposeResult:
        yield Static(f"Coroutine raised {exception.__qualname__}: {exception}."+"\nStack trace:\n" + "".join(traceback.format_tb(exception.__traceback__)))
    def compose_wait(self):
        yield Widget()
    def compose(self) -> ComposeResult:
        return self.result or self.compose_wait()

