from typing import TYPE_CHECKING
from discord import ChannelType, Guild, TextChannel, Thread
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, ListItem, ListView, OptionList
from textual.widgets.option_list import Option

from tools.misc import find
from widgets.collapsible_list_view import CollapsibleListView
from widgets.message import Chatbox
if TYPE_CHECKING:
    from ..tools.client import Client2
else:
    from tools.client import Client2

class GuildWidget(Widget, can_focus=False):
    DEFAULT_CSS = """
    #channels {
        height: 100%
    }
    """
    def __init__(self, client: Client2):
        super().__init__()
        self.client = client 
        self.guild = None
        self._usr = None

    async def set_guild(self, guild: Guild):
        self.guild = guild
        self._usr = self.guild.get_member(self.client.user.id) or await self.guild.fetch_member(self.client.user.id)
        await self.recompose()

    async def on_list_view_selected(self, e: ListView.Selected):
        i = int((e.item.id or "channel_0").removeprefix("channel_"))
        c = find(self.guild.channels, lambda x: x.id==i)
        if isinstance(c, TextChannel) or isinstance(c, Thread):
            await self.get_child_by_type(Horizontal).get_child_by_type(Chatbox).set_channel(c)

    def compose(self) -> ComposeResult: 
        if self.guild != None:
            assert self._usr != None
            with Horizontal() as h:
                h.styles.height = "100%"
                h.styles.width = "100%"
                yield ListView(*(ListItem(Label(i.name), id=f"channel_{i.id}") for i in self.guild.channels if i.type != ChannelType.category and i.permissions_for(self._usr).view_channel),id="channels",classes="primary") 
                yield Chatbox(self.client)
        else:
            yield Container()

