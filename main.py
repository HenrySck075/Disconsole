from datetime import datetime
import traceback

import selfcord

from typing import Any, TypeVar, Generic, TypedDict
import asyncio, os

from selfcord.colour import Color
os.environ["PROMPT_TOOLKIT_COLOR_DEPTH"] = "DEPTH_24_BIT"
from nullsafe import undefined,_
import help
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout, Window, HSplit, VSplit, ScrollablePane, FormattedTextControl, WindowAlign, BufferControl
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.formatted_text import PygmentsTokens
from prompt_toolkit.styles.pygments import style_from_pygments_cls

_KT = TypeVar("_KT",contravariant=True)
_VT = TypeVar("_VT",contravariant=True)

tc = help.ThemeColors()

class TypingList(list):
    def __init__(self, *ok):
        super().__init__(*ok)

    def __setitem__(self, k: int, v: selfcord.User | selfcord.Member):
        list.__setitem__(self,k,v)
class DefaultDict(dict, Generic[_KT,_VT]):
    def __init__(self, map, default:_VT = None):
        super().__init__(map)
        self.default_value = default

    def __getitem__(self, __key: _KT) -> _VT: # pyright: ignore
        try:
            return super().__getitem__(__key)
        except KeyError: return self.default_value
# session states
mode = 0 # 0 for cmd, 1 for input, 2 for scrolling
scrollTarget = ""
scrollCursorPos = DefaultDict[str,int]({},0)
focusingG = 0
focusingCh = 0
lastUser = 0
guilds = []
# TODO: turn these into dict to store objects when switching to other
channels = []
messages = []
widgetIndex = {
    "guilds": [],
    "channels": [],
    "messages": []
}
class a(TypedDict):
    guild: DefaultDict[int,str]
    dm: DefaultDict[int,str]
userColorsCache:dict[int,a] = {}

def get_user_color(user:selfcord.Member|selfcord.User, guild_id:int, force=False) -> str:
    """
    NOTE: there's no fucking way discord gonna give us the color when we spam it

    :param force: Force fetching user color
    """
    global userColorsCache
    if user.id not in userColorsCache:
        userColorsCache[user.id] = {"dm":DefaultDict[int,str]({}), "guild":DefaultDict[int,str]({})} # pyright: ignore
    id = 0 
    root=DefaultDict[int,str]({}) # pyright: ignore
    if type(user) == selfcord.Member:
        id = guild_id #pyright: ignore
        root = userColorsCache[user.id]["guild"]
    elif type(user) == selfcord.User:
        return "#95a5a6"
    else:
        raise TypeError("watch your tone (`user` is not a Member or User)")

    if root[id] == None or force:
        ret = root[id] = user.color.__str__()
        if ret == Color(0).__str__(): ret = "#95a5a6"
        return ret
    else: return root[id]


def render_guilds(x=0):
    global guilds, windows
    guilds = [(i.name, i.id) for i in client.guilds]
    gwin = windows["guilds"] 
    container = []
    for i in guilds:
        container.append(Window(FormattedTextControl(i[0]),width=12,height=1))
    # gwin.refresh(0,0,x,0,curses.LINES-1+x,9)
    gwin.content.children = container # pyright: ignore
    app._redraw()

async def render_channels(gid:int):
    global channels, windows
    h: selfcord.Guild = client.get_guild(gid) # pyright: ignore
    thisUser: selfcord.Member = h.get_member(client.user.id)# pyright: ignore
    ch = h.channels # pyright: ignore
    cwin = windows["channels"]
    container = [None]*len(ch) # type: list[Window] # pyright: ignore
    channels = [None]*len(ch) # type: list[selfcord.abc.GuildChannel] #pyright: ignore
    for i in ch:
        if i.permissions_for(thisUser).view_channel == False: continue
        chIcon = ""
        match i.type.value:
            case 0: chIcon = "\uf4df"
            case 1: chIcon = "\uf456"
            case 2: chIcon = "\ue638"
            case 4: chIcon = "\U000f035d"
            case 5: chIcon = "\U000f00e6"
            case 10 | 11 | 12: chIcon = "\u251c"
            case 13: chIcon = "\U000f1749"
            case 15: chIcon = "\U000f028c"
        
        if "music" in i.name: chIcon = "\U000f02cb"
        container[i.position] = Window(FormattedTextControl(chIcon+" "+i.name),width=22,height=1)
        channels[i.position] = i # pyright: ignore
    channels = list(filter(lambda h: h is not None, channels))
    container = list(filter(lambda h: h is not None, container))

    cwin.content.children = container # pyright: ignore
    app._redraw()

async def add_colors_later(h: dict[selfcord.Member|selfcord.User, list[Window]],guild_id:int|None):
    await asyncio.sleep(2)
    if guild_id == None: return
    for i in h.keys():
        col = get_user_color(i,guild_id)
        for j in h[i]:
            j.content.text[0] = ("fg:"+col+" bold",i.display_name+"              ") # pyright: ignore
    # should be reasonable to invalidate ui now
    app.invalidate()
async def create_msg_window(i: selfcord.Message, notify_on_mention=False, kwargs=[]):
    global userColorsCache

    if i.content != "":
        h=HSplit([
            Window(FormattedTextControl(PygmentsTokens(await help.format_message(client, i))),wrap_lines=True)
        ])
    else:
        h=HSplit([])
    for attach in i.attachments:
        h.children.append(Window(FormattedTextControl("\U000f0066 "+attach.url,tc.url)))
    w = Window(FormattedTextControl([
        ("fg:#95a5a6"+" bold",i.author.display_name+"              "),
        ("fg:gray",i.created_at.strftime("%m/%d/%Y, %H:%M:%S"))
    ],focusable=True),height=1)
    kwargs.append(i,w)
    h.children.insert(0, w)
    if (msgref:=i.reference) is not None:
        msg = msgref.resolved
        if type(msg) == selfcord.Message:
            h.children.insert(0, Window(FormattedTextControl([
                ("","\U000f0772"),
                ("fg:#95a5a6", msg.author.display_name),
                ("fg:gray",msg.content)
            ]),height=1))
        else:
            h.children.insert(0, Window(FormattedTextControl([
                ("","\U000f0772"),
                ("italic fg:gray","Cannot load the message." if type(msg) == None else "Original message was deleted.")
            ])))
    if client.user in i.mentions:
        h.style = tc.msgMentionHighlight
        if notify_on_mention: help.push_notification(i.channel.guild.name + " #"+i.channel.name, i.content) # pyright: ignore
    return h

async def render_messages(channel:selfcord.abc.MessageableChannel, oldContainer = []):
    global messages, windows, lastUser
    messages = [i async for i in channel.history(limit = 50)]
    container = []
    idx = 0
    rust:dict[selfcord.Member|selfcord.User, list[Window]] = {}
    "list of messages needs to have user colors resolved (not counting reply widget)"
    for i in messages.__reversed__():
        if i.author not in rust: rust[i.author] = []
        h = await create_msg_window(i,False,rust[i.author])
        container.append(h)
        widgetIndex["messages"].append(i.id)
        idx+=1
    asyncio.ensure_future(add_colors_later(rust,channel.guild_id)) # pyright: ignore
    container.extend(oldContainer)
    mwin = windows["messageContent"]
    mwin.content.children = container # pyright: ignore
    app.layout.focus(container[-1])
    app._redraw()

def keybind_lore():
    kb = KeyBindings()

    @kb.add("s","g", filter=Condition(lambda: mode == 0))
    def scrollGuild(e: KeyPressEvent):
        global scrollTarget, mode
        scrollTarget = "guilds"
        mode = 2
        windows[scrollTarget].content.get_children()[scrollCursorPos[scrollTarget]].style = tc.selectHighlight # pyright: ignore

    @kb.add("s","c", filter=Condition(lambda:len(channels)!=0))
    def scrollChannel(e: KeyPressEvent):
        global scrollTarget, mode
        scrollTarget = "channels"
        mode = 2
        st = scrollTarget+"_"+str(focusingG)
        windows[scrollTarget].content.get_children()[scrollCursorPos[st]].style = tc.selectHighlight # pyright: ignore

    @kb.add("s","m", filter=Condition(lambda:len(messages)!=0))
    def scrollMessages(e: KeyPressEvent):
        global scrollTarget, mode
        scrollTarget = "messageContent"
        mode = 2
        st = scrollTarget+"_"+str(focusingCh)
        windows[scrollTarget].content.get_children()[scrollCursorPos[st]].style = tc.msgFocusHighlight # pyright: ignore

    def sup(e: KeyPressEvent):
        global focusingG
        st = scrollTarget+("" if scrollTarget == "guilds" else "_"+str(focusingG))
        if (i:=scrollCursorPos[st]-1) >= 0:
            win = windows[scrollTarget].content.get_children()
            limbo = win[i] # type: Window
            un = win[i+1]
            un.style = "" # pyright: ignore
            limbo.style = tc.selectHighlight if scrollTarget != "messageContent" else tc.msgFocusHighlight # pyright: ignore
            scrollCursorPos[st]-=1
            app.layout.focus(limbo)
    kb.add("up", filter=Condition(lambda: scrollTarget != ""))(sup)
    kb.add("<scroll-up>", filter=Condition(lambda: scrollTarget != ""))(sup)

    def sdown(e: KeyPressEvent):
        global focusingG
        st = scrollTarget+("" if scrollTarget == "guilds" else "_"+str(focusingG))
        if (i:=scrollCursorPos[st]+1) < len((win:=windows[scrollTarget].content.get_children())):
            win[i].style = tc.selectHighlight if scrollTarget != "messageContent" else tc.msgFocusHighlight # pyright: ignore
            win[i-1].style = "" # pyright: ignore
            scrollCursorPos[st]+=1
            app.layout.focus(win[i])
    kb.add("down", filter=Condition(lambda: scrollTarget != ""))(sdown)
    kb.add("<scroll-down>", filter=Condition(lambda: scrollTarget != ""))(sdown)

    @kb.add("enter", filter=Condition(lambda: mode != 1))
    async def click(e):
        global mode, scrollTarget, focusingG, focusingCh
        if mode == 2 and scrollTarget == "guilds":
            await render_channels(guilds[scrollCursorPos[scrollTarget]][1])
            windows[scrollTarget].content.get_children()[scrollCursorPos[scrollTarget]].style=""
            focusingG = guilds[scrollCursorPos[scrollTarget]][1]
            scrollTarget = "channels"
        elif mode == 2 and scrollTarget == "channels":
            st = scrollTarget+("" if scrollTarget == "guilds" else "_"+str(focusingG))
            chInfo = channels[scrollCursorPos[st]]
            await render_messages(chInfo) # pyright: ignore
            focusingCh = chInfo.id
            mode = 2
            scrollTarget="messageContent"
            scrollCursorPos["messageContent_"+str(focusingCh)] = len(windows["messageContent"].content.children)-1

    @kb.add("escape", filter=Condition(lambda: mode != 0))
    def ret(e):
        global mode, scrollTarget, focusingG
        if mode == 2:
            windows[scrollTarget].content.get_children()[scrollCursorPos[scrollTarget]].style=""
            if scrollTarget == "guilds":
                mode = 0 
                scrollTarget = ""
            if scrollTarget == "channels": 
                scrollTarget = "guilds"
            if scrollTarget == "messageContent":
                scrollTarget = "channels"
        if mode == 1:
            mode = 2 
            app.layout.focus(windows["messageContent"].content.children[scrollCursorPos["messageContent_"+str(focusingCh)]])

    @kb.add("i", filter=Condition(lambda: mode != 1 and focusingCh != 0))
    def input(e):
        global mode
        app.layout.focus(windows["messageInput"])
        mode = 1

    @kb.add("c-q")
    async def shut(e: KeyPressEvent):
        e.app.exit()
        await client.close()

    return kb
 
async def main():
    global windows, client, app
    conf = help.loadJson("config.json")
    windows = {
        "guilds": ScrollablePane(HSplit([Window()],style=tc.secondaryBg,width=12),show_scrollbar=False),
        "channels":ScrollablePane(HSplit([Window()],width=22,style=tc.channelListBg),show_scrollbar=False),
        "messageContent":ScrollablePane(HSplit([Window()],style=tc.mainBg), max_available_height=848940300),
        "typing":VSplit([],height=1, style=tc.secondaryBg),
        "VerticalLine": Window(char=" ", style="class:line,vertical-line "+tc.secondaryBg, width=1),
        "messageInput": TextArea(height = 2, style = tc.mainBg+" fg:white",dont_extend_width=True)
    }
    def t(**kwargs):
        buf = Buffer()
        return (Window(BufferControl(buf),**kwargs), buf)
    windows["messages"] = HSplit([windows["messageContent"], windows["messageInput"]], style = tc.mainBg) # pyright: ignore
    windows["typingList"] = Window(FormattedTextControl())
    
    win, buf = t(width=3, height=1, style=tc.secondaryBg)
    windows["typingAnim"] = win
    async def typingAnim():
        seq = [
            "\U000f09de\U000f0765\U000f0765",
            "\U000f0765\U000f09de\U000f0765",
            "\U000f0765\U000f0765\U000f09de",
            "\U000f0765\U000f0765\U000f0765"
        ]
        idx = 0
        while True:
            buf.cursor_position=0
            buf.text=seq[idx]
            await asyncio.sleep(0.5)
            idx += 1 
            if idx == 4: idx = 0
            if app.is_running == False: return

    kb = keybind_lore() 

    lay = Layout(HSplit([HSplit([Window(),Window(FormattedTextControl("\n\U000f066f"),align=WindowAlign.CENTER)]),Window(FormattedTextControl("Loading Disconsole"), height=2, align=WindowAlign.CENTER)],style=tc.mainBg))
    app = Application(lay,full_screen=True,mouse_support=True, key_bindings=kb,style=style_from_pygments_cls(help.DisconsoleStyle))
    
    client = selfcord.Client()

    @client.event 
    async def on_ready():
        mainw = VSplit([
            windows["guilds"],
            windows["VerticalLine"],
            HSplit([
                windows["channels"],
                HSplit([
                    Window(FormattedTextControl(client.user.display_name)),# pyright: ignore
                    Window(FormattedTextControl(client.user.name,style="fg:#6B6F77"))# pyright: ignore
                ], height=2, style=tc.secondaryBg)
            ]),
            windows["VerticalLine"],
            windows["messages"]
        ])
        loop=asyncio.get_event_loop()
        asyncio.ensure_future(typingAnim(),loop=loop)

        app.layout.container = mainw

        app.invalidate()

        render_guilds()

    @client.event
    async def on_message(i: selfcord.Message):
        global lastUser
        if focusingCh == i.channel.id:
            h = await create_msg_window(i,True)
            windows["messageContent"].content.children.append()
            lastUser = i.author.id
            app.invalidate()

            app.layout.focus(h)

    @client.event
    async def on_message_delete(msg: selfcord.Message):
        global messages, windows
        if msg.channel.id != focusingCh: return
        index = widgetIndex["messages"].index(msg.channel.id)
        del messages[index]
        windows["messageContent"].content.children.__delitem__(index)
        app.invalidate()

    @client.event 
    async def on_typing(ch: selfcord.TextChannel, usr: selfcord.Member, when: datetime):
        if ch.id == focusingCh:...

    @client.event
    async def on_error(*no, **noo):
        traceback.print_exc(file=open("tb","a"))
    with patch_stdout(): await asyncio.wait([asyncio.create_task(client.start(token=conf["token"])), asyncio.create_task(app.run_async())])# pyright: ignore

asyncio.run(main())
