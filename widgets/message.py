from typing import TYPE_CHECKING
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widget import Widget
from textual.message import Message as TextualMessage
from discord import Client, Color, DMChannel, GroupChannel, Message as DiscordMessage, TextChannel, Thread
from textual.widgets import Label, Markdown, TextArea
if TYPE_CHECKING:
    from ..tools.datetime import datetimeparse
    from ..tools import getThemeColors,color2hex
    from ..tools.client import Client2
else:
    from tools.datetime import datetimeparse
    from tools import getThemeColors,color2hex
    from tools.client import Client2
from nullsafe import _

class Message(Widget, can_focus=True):
    BINDINGS = [
        ("f+r", "", "Go to replied message"),
        ("r", "reply()", "Reply")
    ]

    def __init__(self,obj: DiscordMessage, client: Client) -> None:
        super().__init__()
        self._obj = obj
        self._client = client
        self.styles.height = "auto"

        self.user_color = Color.from_rgb(255,255,255)

        self.referenced_message = None
        self.referenced_message_id = 0

    async def get_user_color(self):
        if self._obj.guild != None: #sent from a server, get the color while we can
            self.user_color = (
                self._obj.guild.get_member(self._obj.author.id)
                or
                await self._obj.guild.fetch_member(self._obj.author.id)
            ).top_role.color

    async def get_referenced_message(self):
        if self.referenced_message_id == 0: return 
        if self.referenced_message!=None: return 

        self.referenced_message = await self._obj.channel.fetch_message(self.referenced_message_id)

    async def update_info(self):
        usrcol_old = self.user_color
        refmsg_old = self.referenced_message
        await self.get_user_color()
        await self.get_referenced_message()
        
        if usrcol_old!=self.user_color or refmsg_old!=self.referenced_message:
            await self.recompose()

    def compose(self) -> ComposeResult:
        usrcol = color2hex(self.user_color)
        # User name & timestamp
        t = f"[bold {usrcol}]{self._obj.author.display_name}[/bold {usrcol}] {datetimeparse(self._obj.created_at)} "
        u = self._obj.author

        # Replied message
        ref = self._obj.reference
        if ref != None:
            self.referenced_message = ref.cached_message
            self.referenced_message_id = ref.message_id or 0
            lt = "[gray]\U000f0772[/gray] "
            if self.referenced_message != None:
                lt+="[bold {c}]{u}[/bold {c}] [gray]{l}[/gray]"
            else:
                reason = "Could not load message content."
                if self.referenced_message_id == 0:
                    reason = "Message deleted."
                
                lt+=f"[italic gray]{reason}[/italic gray]"

            yield Label(lt.format(
                c=color2hex(self.referenced_message.author.color if self.referenced_message!=None else Color.default()),
                u=self.referenced_message.author.display_name if self.referenced_message!=None else "",
                l=self.referenced_message.content if self.referenced_message!=None else ""
            ))

        # Header
        tag = ""
        if u.bot: tag = "BOT"
        if u.system: tag = "SYSTEM"
        if tag!="":
            t+="[bg:discord_accent]{t}[/bg:discord_accent]".format(t=tag)


        yield Label(t, id="#msg_header")

        #Content
        yield Markdown(self._obj.content)
        #emojis
    
    class Reply(TextualMessage):
        def __init__(self, id: int, user: tuple[str,str]) -> None:
            super().__init__()
            self.message_id = id
            self.user_render_info = user

    def reply(self):
        self.post_message(self.Reply(self._obj.id, (self._obj.author.display_name, color2hex(self.user_color))))



class Chatbox(Widget):
    DEFAULT_CSS = """
    #msgbox {
        height: auto
    }
    .infobox {
        width: 100%
    }
    #j {
        align-horizontal: right 
    }
    #toggle_mention {
        width: auto
    }
    """
    def __init__(self,client: Client2) -> None:
        super().__init__()
        self.channel: TextChannel | Thread | DMChannel | GroupChannel | None = None
        self.client = client
        self.messages = []
        self.replying_to = None
        async def on_message(msg: DiscordMessage):
            if self.channel != None and msg.channel.id == self.channel.id:

                self.messages.append(Message(msg,client))
                await self.get_child_by_type(VerticalScroll).recompose()

        client.add_listener("message",on_message)
    
    async def get_messages(self):
        j = [Message(i,self.client) async for i in self.channel.history()]
        j.extend(self.messages)
        self.messages = j

    def compose(self) -> ComposeResult:
        if self.channel == None: return
        yield VerticalScroll(*self.messages)
        if getattr(self.channel,"slowmode_delay",0) != 0:
            with Horizontal(classes="infobox"):
                yield Label("Slowmode is enabled. \U000f13ab", id="j")
        if self.replying_to != None:
            with Horizontal(classes="infobox"):
                yield Label("Replying to [bold {c}]{u}[/bold {c}]".format(c=self.replying_to[2], u=self.replying_to[1]))
                yield Label("[discord_accent]@ON[/discord_accent]",id="toggle_mention")
        yield TextArea(tab_behavior="indent", id="msgbox")
    
    async def set_channel(self, channel: TextChannel | Thread | DMChannel | GroupChannel):
        self.channel = channel
        await self.recompose()
    """
    async def on_message_reply(self, e: Message.Reply):
        self.replying_to = (e.message_id, *e.user_render_info)
        await self.recompose() 
    """
