import asyncio, json
import os
from typing import TYPE_CHECKING
from discord import Guild
from textual.app import App, ComposeResult, log
from textual.widgets import Footer, Label, OptionList, Static
from textual.widgets.option_list import Option
from textual.containers import Horizontal, Vertical, VerticalScroll

from tools.colors import set_disconsole_css, set_theme_mode
from widgets.collapsibe_option_list import CollapsibleOptionList
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
        background: $guild;
        height: 100%
    }
    .primary {
        background: rgb(48,49,54)
    }
    .option-list--option-highlighted, .option-list--option-hover {
        background: $highlight
    }
    #channel--selected {
        background: $select
    }
    #channel--read {
        color: rgb(138,142,148)
    }
    Container {
        background: $primary
    }
    """
    def __init__(self):
        super().__init__()
        set_disconsole_css(self)
        self.styles.height = "1vh"
        self._client_inited = False
        self._client = Client2()
        self._cfg = json.load(open("./config.json"))
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

    def get_css_variables(self) -> dict[str, str]:
        return set_disconsole_css(self)
    async def on_ready(self):
        asyncio.ensure_future(self._client.start(self._cfg["token"]),loop=asyncio.get_event_loop())

    def compose_splash(self):
        # U000f066f
        yield Label("Loading Disconsole...")
        yield Label("please i beg you")

    async def on_collapsible_option_list_selected(self,e:OptionList.OptionSelected):
        optl = e.option_list
        if optl.id == "guilds":
            selected_guild = int((e.option.id or "guild_0").removeprefix("guild_"))
            self.selected_guild = (
                self._client.get_guild(selected_guild)
                or 
                await self._client.fetch_guild(selected_guild)
            )
            await self.get_child_by_id("ui").get_child_by_type(GuildWidget).set_guild(self.selected_guild)

    def compose(self) -> ComposeResult:
        log(self._client_inited)
        if self._client_inited:
            with Horizontal(id="ui") as h:
                h.styles.height = "100%"
                yield CollapsibleOptionList([Option(i.name, id=f"guild_{i.id}") for i in self._client.guilds],id="guilds") 
                yield GuildWidget(self._client)
                yield Chatbox(self._client)
            yield Footer() 
        else: 
            return self.compose_splash()

if __name__ == "__main__":
    MApp().run()
