from __future__ import annotations
from typing import Iterable

from rich.repr import Result
from textual.app import ComposeResult, log
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, OptionList
from textual.widgets.option_list import Option, Separator

SubOptionsHeaderType = Option | Widget

class SubOptions:
    def __init__(self, header: SubOptionsHeaderType, *sub_options: OptionType, id:str|None = None, disabled: bool = False) -> None:
        self.id = id
        self.header = header
        self.sub_options = sub_options
        self.disabled = disabled

OptionMessageType = SubOptionsHeaderType | SubOptions
OptionType = OptionMessageType | Separator 

class CollapsibleOptionList(VerticalScroll):
    index = reactive(0)
    DEFAULT_CSS = """
    .coption-list--option-highlighted {
        background: $highlight
    }
    """
    BINDINGS = [
        Binding("up", "move_up", "Scroll Up"),
        Binding("down", "move_down", "Scroll Down"),
        Binding("pageup", "move_page_up", "Page Up"),
        Binding("pagedown", "move_page_down", "Page Down"),
        Binding("enter", "select", "Select"),
    ]
    class OptionMessage(Message):
        """Base class for all option messages."""

        def __init__(self, option_list: CollapsibleOptionList, index: int) -> None:
            """Initialise the option message.

            Args:
                option_list: The option list that owns the option.
                index: The index of the option that the message relates to.
            """
            super().__init__()
            self.option_list = option_list
            """The option list that sent the message."""
            self.option = option_list.get_option_at_index(index)
            """The highlighted option."""
            self.option_id: str | None = self.option.id
            """The ID of the option that the message relates to."""
            self.option_index: int = index
            """The index of the option that the message relates to."""

        @property
        def control(self) -> CollapsibleOptionList:
            """The option list that sent the message.

            This is an alias for [`OptionMessage.option_list`][textual.widgets.OptionList.OptionMessage.option_list]
            and is used by the [`on`][textual.on] decorator.
            """
            return self.option_list

        def __rich_repr__(self) -> Result:
            yield "option_list", self.option_list
            yield "option", self.option
            yield "option_id", self.option_id
            yield "option_index", self.option_index

    class Highlighted(OptionMessage):
        """Message sent when an option is highlighted.

        Can be handled using `on_option_list_option_highlighted` in a subclass of
        `OptionList` or in a parent node in the DOM.
        """

    class Selected(OptionMessage):
        """Message sent when an option is selected.

        Can be handled using `on_option_list_option_selected` in a subclass of
        `OptionList` or in a parent node in the DOM.
        """
    
    def get_option_at_index(self, index: int) -> OptionMessageType:
        return self.options[self._selectable_options[index][1]] # type: ignore

    def __init__(self, options: list[OptionType], name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.options = options
        self._selectable_options: list[tuple[Widget,int]] = []
        self._headers = []
        self._idx = 0
        "the real item index on the options list"

    def validate_index(self, idx:int):
        if idx < 0:
            idx = 0
        m = len(self._selectable_options)
        if idx >= m:
            idx = m-1
        return idx

    def watch_index(self,old:int,new:int):
        log(f"old: {old} | new: {new}")
        self.idx = self._selectable_options[new][1]
        self._selectable_options[old][0].remove_class("coption-list--option-highlighted")
        self._selectable_options[new][0].add_class("coption-list--option-highlighted")
        self.post_message(self.Highlighted(self, new))
        self.scroll_to(y=new) 

    def _action_move_down(self):
        "Not scroll_down because it highlights below item"
        self.index+=1
    def _action_move_up(self):
        "Not scroll_up because it highlights above item"
        self.index-=1
    def _action_move_page_up(self):
        "bro lowercasebeef singlehandedly made a windows x gd collab out of nowhere"
        self.index-=self.container_size.height
    def _action_move_page_down(self):
        "adaf port ur shit !!"
        self.index+=self.container_size.height
    def _action_select(self):
        self.post_message(self.Selected(self, self.index))
        
        opt = self.options[self._selectable_options[self.index][1]]
        if isinstance(opt, SubOptions):
            ...
            

    def compose_options(self, options:Iterable[OptionType]) -> ComposeResult:
        a = self._selectable_options.append
        for idx, option in enumerate(options):
            if isinstance(option, Widget):
                if not option.disabled: a((option,idx))
                yield option
            elif isinstance(option, Option):
                l = Label(option.prompt, disabled=option.disabled)
                if not option.disabled: a((l,idx))
                yield l
            elif isinstance(option, SubOptions):
                continue
                l = Label(option.header.prompt) if isinstance(option.header, Option) else option.header
                if not option.disabled:
                    a((l,idx))
                    # Any custom header widgets added to this may implement "expanded" parameter because it won't be used again anyways
                    self._headers.append((l,idx,False))
                    yield l 
                    yield from self.compose_options(option.sub_options)
        log(self._selectable_options)

    def compose(self) -> ComposeResult:
        return self.compose_options(self.options)
        
