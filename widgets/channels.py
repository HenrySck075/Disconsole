from typing import TYPE_CHECKING
from discord import ChannelType, Guild
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.containers import Container, Vertical, VerticalScroll
from textual.widgets import Label, ListItem, ListView, OptionList
from textual.widgets.option_list import Option

from widgets.collapsible_list_view import CollapsibleListView
if TYPE_CHECKING:
    from ..tools.client import Client2
else:
    from tools.client import Client2

class GuildWidget(Widget, can_focus=True):
    def __init__(self, client: Client2):
        super().__init__()
        self.client = client 
        self.guild = None

    async def set_guild(self, guild: Guild):
        self.guild = guild
        await self.recompose()

    def compose(self) -> ComposeResult: 
        if self.guild != None:
            yield CollapsibleListView(*(ListItem(Label(i.name), id=f"channel_{i.id}") for i in self.guild.channels if i.type != ChannelType.category),id="channels",classes="primary") 
        else:
            yield Container()

