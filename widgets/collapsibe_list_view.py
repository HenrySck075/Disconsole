from __future__ import annotations
from __future__ import annotations
from enum import Enum
from operator import index
from typing import Iterable

from rich.repr import Result
from textual.app import ComposeResult, log
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, ListItem, ListView

class SublistExitDirection(Enum):
    Top = 0
    Bottom = 1

class SubListItems(Widget,can_focus=False):
    index = reactive[int|None](None) # does not handle touching :3
    def __init__(self, header: ListItem, *sub_items: ListItemType, id:str|None = None, expanded: bool = False) -> None:
        super().__init__(id=id)
        self.header = header
        self.sub_items = sub_items
        self.expanded = expanded

    class SublistExited(Message):
        def __init__(self, steps: int) -> None:
            super().__init__()
            self.direction = SublistExitDirection.Top if steps < 0 else SublistExitDirection.Bottom
            "Which way the user exited the sublist"
            self.steps = abs(steps)
            "how much"

    def compose(self):
        yield self.header
        yield from self.sub_items

    def _validate_index(self, v:int|None):
        if v==None: 
            # this was requested to unselect, just do it and not send any messages
            return v
        if self.index != None: # if it's already exited, don't even try
            if v<0 or v>=(len(self.sub_items)+1 if self.expanded else 1):
                if self.post_message(self.SublistExited(v)): return None 
            return v
    def _get_item(self, idx):
        if idx == 0: return self.header
        else: return self.sub_items[idx]

    def _watch_index(self, old, new):
        # Don't do anything about SubListItems
        # Speech bubble
        if new == None:
            i = self._get_item(old)
            if isinstance(i, ListItem):
                i.highlighted = False
        
        if old == None:
            i = self._get_item(new)
            if isinstance(i, ListItem):
                i.highlighted = True

    def cursor_up(self):
        if self.index!=None: 
            d = self._get_item(self.index)
            if isinstance(d, SubListItems): d.cursor_up()
            else: self.index-=1
    def cursor_down(self):
        if self.index!=None: 
            d = self._get_item(self.index)
            if isinstance(d, SubListItems): d.cursor_down()
            else: self.index+=1
    
ListItemType = ListItem | SubListItems


class CollapsibleListView(ListView):
    def __init__(self, *children: ListItem, initial_index: int | None = 0, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False) -> None:
        super().__init__(*children, initial_index=initial_index, name=name, id=id, classes=classes, disabled=disabled)

