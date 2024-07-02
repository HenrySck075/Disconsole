from typing import Generic, TypeVar

from textual.app import ComposeResult
from textual.widget import Widget


T = TypeVar("T")


class DataHolder(Widget, Generic[T]):
    "A widget that holds some data belong to a widget"
    def __init__(self, widget: Widget, data: T, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.widget = widget 
        self.data = data

    def compose(self) -> ComposeResult:
        yield self.widget
