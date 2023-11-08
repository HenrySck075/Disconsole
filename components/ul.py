from typing import Callable, Sequence
from prompt_toolkit.key_binding import KeyBindingsBase
from prompt_toolkit.layout import AnyContainer, AnyDimension, Container, Dimension, HSplit, VerticalAlign, sum_layout_dimensions
from prompt_toolkit.layout.screen import WritePosition

class Component(HSplit):
    "Same as HSplit but without the children heights expanded"
    def __init__(self, children: Sequence[AnyContainer], window_too_small: Container | None = None, align: VerticalAlign = VerticalAlign.JUSTIFY, padding: AnyDimension = 0, padding_char: str | None = None, padding_style: str = "", width: AnyDimension = None, height: AnyDimension = None, z_index: int | None = None, modal: bool = False, key_bindings: KeyBindingsBase | None = None, style: str | Callable[[], str] = "") -> None:
        super().__init__(children, window_too_small, align, padding, padding_char, padding_style, width, height, z_index, modal, key_bindings, style)

    def _divide_heights(self, write_position: WritePosition) -> list[int] | None:
        if not self.children: return []
        width = write_position.width
        height = write_position.height
        dim = [c.preferred_height(width, height) for c in self._all_children]
        sum_dimensions = sum_layout_dimensions(dim)

        return [d.max for d in dim] if sum_dimensions.min <= height else None 

    @classmethod
    async def create(cls,*args,**kw):
        return cls(*args,**kw)
 
