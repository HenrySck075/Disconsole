import asyncio, json
import os
from typing import TYPE_CHECKING
from discord import Guild
from rich.theme import Theme
from textual.app import App, ComposeResult
from textual.widgets import Footer, OptionList, Static
from textual.widgets.option_list import Option
from textual.containers import Horizontal, Vertical, VerticalScroll
# intriguing
if TYPE_CHECKING:
    from .tools.client import Client2 
    from .widgets.channels import GuildWidget
    from .widgets.message import Chatbox
else:
    from tools.client import Client2 
    from widgets.channels import GuildWidget
    from widgets.message import Chatbox
from nullsafe import undefined, _

class MApp(App):
    CSS = """
    #guilds, #channels {
        width: 17;
        border: none
    }
    #userbox {
        height: 3
    }
    #guilds {
        background: rgb(33,34,38)
    }
    .primary {
        background: rgb(48,49,54)
    }
    .option-list--option-highlighted, .option-list--option-hover {
        background: rgb(59,60,65)
    }
    #channel--selected {
        background: rgb(66,70,78)
    }
    #channel--read {
        color: rgb(138,142,148)
    }
    """
    def __init__(self):
        super().__init__()
        self._client_inited = False
        self._client = Client2()
        self._cfg = json.load(open("./configs.json"))
        self.channels_list = []

        self.selected_channel = None
        self.selected_guild = None
 
        async def discord_on_ready():
            self._client_inited = True
            await self.recompose() # j

        async def discord_on_guild_join(g:Guild): 
            self.get_widget_by_id("guilds",OptionList).add_option(Option(g.name,f"guild_{g.id}"))

        self._client.add_listener("ready",discord_on_ready)
        self._client.add_listener("guild_join",discord_on_guild_join)

    async def on_ready(self):
        asyncio.ensure_future(self._client.start(os.getenv("disconsole_token","")),loop=asyncio.get_event_loop())

    def compose_splash(self):
        # U000f066f
        yield Static("Loading Disconsole...")

    async def on_option_list_option_selected(self, optl: OptionList, idx: int):
        if optl.id == "guilds":
            selected_guild = int((optl.get_option_at_index(idx).id or "guild_0").removeprefix("guild_"))
            self.selected_guild = (
                self._client.get_guild(selected_guild)
                or 
                await self._client.fetch_guild(selected_guild)
            )
            self.channels_list = self.selected_guild.channels
            await self.get_widget_by_id("channels_userbox").recompose()


    def compose(self) -> ComposeResult:
        if self._client_inited:
            with Horizontal(id="ui"):
                yield OptionList(*(Option(i.name, id=f"guild_{i.id}") for i in self._client.guilds),id="guilds",wrap=False) 
                if self.selected_guild!=None:
                    yield GuildWidget(self.selected_guild,self._client)
                if self.selected_channel!=None:
                    yield Chatbox(self.selected_channel,self._client)
            yield Footer()
                
        else: 
            return self.compose_splash()

if __name__ == "__main__":
    MApp().run()
