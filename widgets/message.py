import asyncio
from typing import TYPE_CHECKING
from rich.console import RenderableType
from textual.app import ComposeResult, log
from textual.containers import Container, Horizontal, VerticalScroll
from textual.events import Key, Resize
from textual.reactive import reactive, var
from textual.widget import Widget
from textual.message import Message as TextualMessage
from discord import Client, Color, DMChannel, GroupChannel, Message as DiscordMessage, TextChannel, Thread
from textual.widgets import Label, ListItem, ListView, Markdown, TextArea
if TYPE_CHECKING:
    from ..tools.datetime import datetimeparse
    from ..tools import getThemeColors,color2hex
    from ..tools.client import Client2
    from ..tools.caches import colorCaches 
else:
    from tools.datetime import datetimeparse
    from tools import getThemeColors,color2hex
    from tools.client import Client2
    from tools.caches import colorCaches 
from nullsafe import _

class ChatboxReal(TextArea):
    def __init__(self, text: str = "", *, language: str | None = None, theme: str = "css", soft_wrap: bool = True, read_only: bool = False, show_line_numbers: bool = False, max_checkpoints: int = 50, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False, tooltip: RenderableType | None = None) -> None:
        super().__init__(text, language=language, theme=theme, soft_wrap=soft_wrap, tab_behavior="indent", read_only=read_only, show_line_numbers=show_line_numbers, max_checkpoints=max_checkpoints, name=name, id=id, classes=classes, disabled=disabled, tooltip=tooltip)
        self.multiline = False
        "Whether we are in multiline mode or not, which toggling and later submitting can be done by sending ctrl+s"

    class Submitted(TextualMessage):
        def __init__(self, content: str) -> None:
            super().__init__()
            self.content = content

    async def _on_key(self, event: Key) -> None:
        if (event.key == "enter" and not self.multiline) or (event.key == "ctrl+s" and self.multiline):
            self.post_message(self.Submitted(self.text))
            self.clear()
            event.prevent_default()
            self.multiline = False
        if event.key == "ctrl+s" and not self.multiline:
            self.multiline = True
            self.text+="\n"
            event.prevent_default()

class Message(Widget, can_focus=True):
    BINDINGS = [
        ("f+r", "", "Go to replied message"),
        ("r", "reply", "Reply")
    ]


    def __init__(self,obj: DiscordMessage, client: Client) -> None:
        super().__init__(id=f"message_{obj.id}")
        self._obj = obj
        self._client = client
        self.styles.height = "auto"
        self.styles.width = "100%"

        self.user_color: str = colorCaches[self._obj.guild.id].get(self._obj.author.id,"#ffffff") if self._obj.guild != None else "#ffffff"

        self.referenced_message = None
        self.referenced_message_id = 0


        self._info_updated = (False,False)

    async def get_user_color(self):
        if self._obj.guild != None: #sent from a server, get the color while we can
            try:
                self.user_color = colorCaches[self._obj.guild.id].get(self._obj.author.id,"")
                if self.user_color=="":
                    self.user_color = color2hex((
                        self._obj.guild.get_member(self._obj.author.id)
                        or
                        await self._obj.guild.fetch_member(self._obj.author.id)
                    ).top_role.color)
                    colorCaches[self._obj.guild.id].set(self._obj.author.id, self.user_color)
            except: # deleted users and webhooks
                self.user_color = "#ffffff"

    async def get_referenced_message(self):
        if self.referenced_message_id == 0: return 
        if self.referenced_message!=None: return 

        self.referenced_message = self._obj.reference.cached_message or await self._obj.channel.fetch_message(self.referenced_message_id)

    async def update_info(self):
        await asyncio.sleep(0.5)
        usrcol_old = self.user_color
        refmsg_old = self.referenced_message
        if not self._info_updated[0]: await self.get_user_color()
        if not self._info_updated[1]: await self.get_referenced_message()
        
        self._info_updated = (usrcol_old!=self.user_color, refmsg_old!=self.referenced_message)
        if any(self._info_updated):
            await self.recompose()

    def compose(self) -> ComposeResult:
        
        usrcol = self.user_color 
        # User name & timestamp
        t = f"[bold {usrcol}]{self._obj.author.display_name}[/bold {usrcol}] {datetimeparse(self._obj.created_at)} "
        u = self._obj.author

        # Replied message
        ref = self._obj.reference
        if ref != None:
            
            self.referenced_message = self.referenced_message or ref.cached_message
            self.referenced_message_id = ref.message_id or self.referenced_message_id
            lt = "[gray]\U000f0772[/gray] "
            if self.referenced_message != None:
                lt+="[bold {c}]{u}[/bold {c}] [grey]{l}[/grey]"
            else:
                reason = "Could not load message content."
                if self.referenced_message_id == 0:
                    reason = "Message deleted."
                
                lt+=f"[italic grey]{reason}[/italic grey]"
            c = colorCaches[self._obj.guild.id or 0].get(self._obj.author.id)
            if c==None:
                c = color2hex(self.referenced_message.author.color if self.referenced_message!=None else Color.default())
                colorCaches[self._obj.guild.id or 0][self._obj.author.id] = c
            yield Label(lt.format(
                c=c,
                u=self.referenced_message.author.display_name if self.referenced_message!=None else "",
                l=self.referenced_message.content if self.referenced_message!=None else ""
            ))

        # Header
        tag = ""
        if u.bot: tag = "BOT"
        if u.system: tag = "SYSTEM"
        if tag!="":
            t+="[bg:discord_accent]{t}[/bg:discord_accent]".format(t=tag)


        yield Label(t, id="msg_header")

        #Content
        log(self._obj.content)
        m = Markdown(self._obj.content.removesuffix("\n"))
        m.styles.margin = 0
        
        yield m
        #emojis

        if not all(self._info_updated): 
            "a"
            self.run_worker(self.update_info())
    
    class Reply(TextualMessage):
        def __init__(self, id: int, user: tuple[str,str]) -> None:
            super().__init__()
            self.message_id = id
            self.user_render_info = user

    def reply(self):
        self.post_message(self.Reply(self._obj.id, (self._obj.author.display_name, self.user_color)))



class Chatbox(Widget):
    DEFAULT_CSS = """
    #msgbox {
        height: auto;
        min-height: 3;
        border: solid $contrast
    }
    .infobox {
        width: 100%;
        height: 1
    }
    #j {
        align-horizontal: right 
    }
    #toggle_mention {
        width: auto
    }
    Markdown {
        max-width: 30
    }

    """
    messages_list_height = var(10)
    def __init__(self,client: Client2) -> None:
        super().__init__()
        self.channel: TextChannel | Thread | DMChannel | GroupChannel | None = None
        self.client = client
        self.messages = []
        self.replying_to = None
        self.styles.height = "100%"
        self.styles.width = "100%"

        self._await_scroll = False


        async def on_message(msg: DiscordMessage):
            if self.channel != None and msg.channel.id == self.channel.id:
                m = Message(msg,client)
                self.messages.append(m)
                l = ListItem(m)
                self.get_child_by_type(ListView).append(l)
                if self._await_scroll and msg.author.id == self.client.user.id:
                    l.scroll_visible()
                    self._await_scroll = False

        async def on_message_edit(before: DiscordMessage, after: DiscordMessage):
            if self.channel != None and before.channel.id == self.channel.id:
                try:
                    self.get_child_by_id(f"message_{before.id}",Message).get_child_by_type(Markdown).update(after.content)
                except:
                    pass

        client.add_listener("message",on_message)
        client.add_listener("message_edit",on_message_edit)
    
    async def get_messages(self):
        assert self.channel != None
        j = [ListItem(Message(i,self.client)) async for i in self.channel.history(limit=15)]
        self.get_child_by_type(ListView).extend(reversed(j))

    def _watch_messages_list_height(self, v:int):
        try:
            self.get_child_by_type(ListView).styles.height = v
        except:
            pass
    async def on_resize(self, e: Resize):
        s = e.size
        try:
            self.messages_list_height = s.height - self.get_child_by_type(TextArea).size.height
        except: pass

    async def on_chatbox_real_submitted(self,e:ChatboxReal.Submitted):
        assert self.channel != None
        await self.channel.send(e.content)
        self._await_scroll = True

    def compose_messagable(self) -> ComposeResult:
        "For messagable channels"
        if self.channel != None:
            yield ListView()
            if getattr(self.channel,"slowmode_delay",0) != 0:
                with Horizontal(classes="infobox"):
                    yield Label("Slowmode is enabled. \U000f13ab", id="j")
            if self.replying_to != None:
                with Horizontal(classes="infobox"):
                    yield Label("Replying to [bold {c}]{u}[/bold {c}]".format(c=self.replying_to[2], u=self.replying_to[1]))
                    yield Label("[discord_accent]@ON[/discord_accent]",id="toggle_mention")
            yield ChatboxReal(id="msgbox")
        else:
            yield Container()

    def compose(self) -> ComposeResult:
        return self.compose_messagable()
        
    async def set_channel(self, channel: TextChannel | Thread | DMChannel | GroupChannel):
        # code will still works for channel types not included here if it does have texting support (aka have the history function)
        self.channel = channel
        await self.recompose()
        await self.get_messages()
        l = self.get_child_by_type(ListView)
        # l.children[0].scroll_visible(False)
        l.index = len(l.children)-1
    """
    async def on_message_reply(self, e: Message.Reply):
        self.replying_to = (e.message_id, *e.user_render_info)
        await self.recompose() 
    """
