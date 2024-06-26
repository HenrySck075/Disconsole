import asyncio
from typing import TYPE_CHECKING
from discord import Guild
from textual.reactive import reactive
from textual.widget import Widget
from textual.containers import Container, Vertical
from textual.widgets import OptionList
from textual.widgets.option_list import Option
if TYPE_CHECKING:
    from ..tools.client import Client2
else:
    from tools.client import Client2

class GuildWidget(Widget):
    def __init__(self, guild: Guild, client: Client2):
        super().__init__()
        self.client = client 
        self.guild = guild

    def compose(self): 
        yield OptionList(*(Option(i.name, id=f"channel_{i.id}") for i in self.guild.channels),id="channels",classes="primary",wrap=False)

