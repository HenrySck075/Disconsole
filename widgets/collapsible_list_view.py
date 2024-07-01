from __future__ import annotations
from __future__ import annotations
from enum import Enum

from rich.repr import Result
from textual.app import ComposeResult, log
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, ListItem, ListView
from textual import _widget_navigation

class SublistExitDirection(Enum):
    Top = 0
    Bottom = 1

class SubListItems(Widget,can_focus=False):
    index = reactive[int|None](None)
    expanded = reactive(True, recompose=True)

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

    def _on_list_item__child_clicked(self, e: ListItem._ChildClicked):
        e.stop() # dont propangate or the parent will set a wrong index
        try: self.index = self.sub_items.index(e.item)
        except: self.index = 0 # it's the header that called the event
        if self.index == 0:
            self.expanded = False

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

    def _watch_index(self, old:int|None, new:int|None):
        # Don't do anything about SubListItems
        # ____  ______________________________
        #     \/
        #   stupid individual (me yesterday)

        # nuh uh we still have to notify them to unselect if the old index is the sublist since were in that previously
        if old!=None and new!=None:
            o = self._get_item(old)
            n = self._get_item(new)
            # watch method is not called if old is the same as new so we don't need any further checks
            if isinstance(n, ListItem): n.highlighted = True
            if isinstance(o, SubListItems):
                o.index = None
            else:
                o.highlighted = False

    def cursor_up(self):
        if self.index!=None: 
            d = self._get_item(self.index)
            if isinstance(d, SubListItems): d.cursor_up()
            else: 
                self.index-=1
                d = self._get_item(self.index)
                if isinstance(d, SubListItems): d.index = len(d.sub_items) if d.expanded else 0
    def cursor_down(self):
        if self.index!=None: 
            d = self._get_item(self.index)
            if isinstance(d, SubListItems): d.cursor_down()
            else: 
                self.index+=1
                d = self._get_item(self.index)
                if isinstance(d, SubListItems): d.index = 0

ListItemType = ListItem | SubListItems

class CollapsibleListView(ListView):
    class NodeHighlighted(Message):
        """Posted when the highlighted item changes.

        Highlighted item is controlled using up/down keys.
        Can be handled using `on_list_view_highlighted` in a subclass of `ListView`
        or in a parent widget in the DOM.
        """

        ALLOW_SELECTOR_MATCH = {"item"}
        """Additional message attributes that can be used with the [`on` decorator][textual.on]."""

        def __init__(self, list_view: CollapsibleListView | SubListItems, item: ListItemType | None) -> None:
            super().__init__()
            self.list_view: CollapsibleListView | SubListItems = list_view
            """The view that contains the item highlighted."""
            self.item = item
            """The highlighted item, if there is one highlighted."""

    class NodeSelected(Message):
        """Posted when a list item is selected, e.g. when you press the enter key on it.

        Can be handled using `on_list_view_selected` in a subclass of `ListView` or in
        a parent widget in the DOM.
        """

        ALLOW_SELECTOR_MATCH = {"item"}
        """Additional message attributes that can be used with the [`on` decorator][textual.on]."""

        def __init__(self, list_view: CollapsibleListView | SubListItems, item: ListItemType) -> None:
            super().__init__()
            self.list_view: CollapsibleListView | SubListItems = list_view
            """The view that contains the item selected."""
            self.item: ListItemType = item
            """The selected item."""


    def __init__(self, *children: ListItemType, initial_index: int | None = 0, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False) -> None:
        super(VerticalScroll, self).__init__(*children, name=name, id=id, classes=classes, disabled=disabled)
        """
        self._index = _widget_navigation.find_next_enabled(
            children,
            # What the fuck is this dude
            anchor=initial_index if initial_index is not None else None,
            direction=1,
            with_anchor=True,
        )
        """
        self._index = initial_index



    def watch_index(self, old_index: int | None, new_index: int | None) -> None:
        """Updates the highlighting when the index changes."""
        if self._is_valid_index(old_index):
            old_child = self._nodes[old_index]
            if isinstance(old_child, ListItem): old_child.highlighted = False

        if self._is_valid_index(new_index) and not self._nodes[new_index].disabled:
            new_child: ListItemType = self._nodes[new_index] # type: ignore
            if isinstance(new_child, ListItem): new_child.highlighted = True
            else: new_child.index = 0
            self._scroll_highlighted_region()
            self.post_message(self.NodeHighlighted(self, new_child))
        else:
            self.post_message(self.NodeHighlighted(self, None))



