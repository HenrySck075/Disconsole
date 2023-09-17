from datetime import datetime
import traceback

import selfcord

from typing import Any, TypeVar, Generic, TypedDict
import asyncio, os

from selfcord.colour import Color
os.environ["PROMPT_TOOLKIT_COLOR_DEPTH"] = "DEPTH_24_BIT"
from nullsafe import undefined,_
import help

import soundfile as sf, sounddevice as sd, numpy as np # audio stuff

from custom_widgets import RoundedFrame as Frame
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.application import Application 
from prompt_toolkit.application.run_in_terminal import in_terminal
from prompt_toolkit.layout import ConditionalContainer, Layout, Window, HSplit, VSplit, FormattedTextControl, WindowAlign, ScrollablePane
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyPressEvent
from prompt_toolkit.key_binding.bindings.mouse import load_mouse_bindings
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
widgetIndex = {
    "guilds": [],
    "channels": [],
    "messages": []
}
widgetData = {
    "guilds": [],
    "channels": [],
    "messages": [],
    "forums": []
}
# dont worry `global` already took care of typecheck deciding availability :thumbsup:
for i in widgetData.keys():
    exec(i+"=widgetData['"+i+"']",globals())

class a(TypedDict):
    guild: DefaultDict[int,str]
    dm: DefaultDict[int,str]
userColorsCache:dict[int,a] = {}

async def get_user_color(user_id:int, guild_id:int, force=False) -> str:
    """
    NOTE: there's no fucking way discord gonna give us the color if it's from on message event

    :param force: Force fetching user color
    """
    user = await help.get_or_fetch(client.get_user,help.MISSING,user_id)
    assert user is not None, "User does not exist"
    global userColorsCache
    if user_id not in userColorsCache:
        userColorsCache[user_id] = {"dm":"", "guild":DefaultDict[int,str]({})} # pyright: ignore
    id = 0 
    root=DefaultDict[int,str]({}) # pyright: ignore
    if type(user_id) != int:
        raise TypeError("henry i thought pyright is that strict (`user` is not int)")
    if guild_id!=0:
        id = guild_id #pyright: ignore
        root = userColorsCache[user_id]["guild"]
    else:
        return "#95a5a6"

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
    global channels, windows, scrollTarget
    h: selfcord.Guild = client.get_guild(gid) # pyright: ignore
    thisUser: selfcord.Member = h.get_member(client.user.id)# pyright: ignore
    ch = h.channels # pyright: ignore
    cwin = windows["channels"]
    container = [None]*len(ch) # type: list[Window] # pyright: ignore
    channels = [None]*len(ch) # type: list[GuildChannel] #pyright: ignore
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
    scrollTarget = "channels"

def sizeof_fmt(num, suffix="B"):
    for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if abs(num) < 1000.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1000.0
    return f"{num:.1f}Y{suffix}"
async def render_attachment(attach: selfcord.Attachment):
    assert attach.content_type is not None
    if "text/" in attach.content_type:
        return Frame(
            HSplit([
                Window(FormattedTextControl((await attach.read()).decode()),height=6),
                Window(FormattedTextControl([
                    ("bold", attach.filename),
                    ("fg:gray", sizeof_fmt(attach.size))
                ]),align=WindowAlign.RIGHT)
            ],style=tc.channelListBg),
            style=tc.channelListBg+" "+tc.secondaryBg.replace("bg","fg")
        )
    if "audio/" in attach.content_type:
        return Frame(
            HSplit([
                Window(FormattedTextControl([
                    (tc.accent, "\uf1c7"),
                    (tc.url, attach.filename),
                    ("fg:gray", sizeof_fmt(attach.size))
                ])),
                VSplit([
                    Window(FormattedTextControl("\U000f040a",style="fg:#A0A0A1")),

                ])
            ],style=tc.channelListBg)
        )
    else: return Window(FormattedTextControl("\U000f0066 "+attach.url,tc.url))

async def create_msg_window(i: selfcord.Message, notify_on_mention=False):
    global userColorsCache
    def conditional_tuple(t:tuple[str,str],f:bool) -> tuple[str,str]:
        return t if f else ("","")
    def cond(h: list[tuple[tuple[str,str],bool]]):
        for i in h:
            if (x:=conditional_tuple(i[0],i[1])) != ("",""): return x 
        return ("","")
    assert i.channel.guild is not None

    if i.content != "":
        h=HSplit([
            Window(FormattedTextControl(PygmentsTokens(await help.format_message(client, i))),wrap_lines=True)
        ])
    else:
        h=HSplit([])
    for attach in i.attachments:
        h.children.append(await render_attachment(attach))
    w = Window(FormattedTextControl([
        ("bold fg:"+await get_user_color(i.author.id,i.channel.guild.id),i.author.display_name+" "),
        cond([((tc.accent,"BOT"),i.author.bot),((tc.accent,"\U000f012c BOT"),i.author.bot and i.author.public_flags.verified_bot),((tc.accent,"SYSTEM"),i.author.system)]),
        ("fg:gray",i.created_at.strftime("%m/%d/%Y, %H:%M:%S"))
    ],focusable=True),height=1)
    h.children.insert(0, w)
    if (msgref:=i.reference) is not None:
        msg = msgref.resolved
        # 1: conditional container is bloatware
        # 2: pyright will shout at me for None
        if type(msg) == selfcord.Message:
            h.children.insert(0, Window(FormattedTextControl([
                ("","\U000f0772"),
                ("bold fg:"+await get_user_color(msg.author.id,i.channel.guild.id), msg.author.display_name+" "),
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

def rf_relative_time(time:datetime):
    diff = datetime.now() - time
    s = diff.seconds
    if diff.days > 30:
        return '>30d ago'
    elif diff.days >= 1:
        return '{}d ago'.format(diff.days)
    elif s <= 1:
        return 'just now'
    elif s < 60:
        return '{}s ago'.format(s)
    elif s < 120:
        return '1m ago'
    elif s < 3600:
        return '{}m ago'.format(s/60)
    elif s < 7200:
        return '1h ago'
    else:
        return '{}h ago'.format(s/3600)

async def render_forums(channel: selfcord.ForumChannel):
    global windows, scrollTarget, forums
    forums = channel.threads 
    container = []
    for i in forums:
        ownmsg = [j async for j in i.history(limit=2, oldest_first=True) if j.id == i.last_message_id]
        if len(ownmsg) == 0: ownmsg = [None]
        container.append(Frame(
            VSplit([
                Window(FormattedTextControl([
                    ("bold: fg:"+await get_user_color(i.owner_id, channel.guild.id),(i.owner.name if i.owner is not None else "")+"  "),
                    ("fg:gray",rf_relative_time([n async for n in i.history(limit=1)][0].created_at))
                ])),
                Window(FormattedTextControl(i.name,style=tc.mainBg+" bold",focusable=True)),
                Window(FormattedTextControl(ownmsg[0].content if ownmsg[0] is not None else ""),height=2),
            ],style=tc.mainBg)
        ))
    win = windows["forums"]
    win.content.children = container
    scrollTarget = "forum"


async def render_messages(channel:help.MessageableChannel, oldContainer = []):
    global scrollTarget
    if type(channel) == selfcord.ForumChannel:
        return await render_forums(channel) # pyright: ignore
    global messages, windows, lastUser, rust
    messages = [i async for i in channel.history(limit = 50)]
    container = []
    "list of messages needs to have user colors resolved (not counting reply widget)"
    for i in messages.__reversed__():
        h = await create_msg_window(i,False)
        container.append(h)
        widgetIndex["messages"].append(i.id)
    container.extend(oldContainer)
    mwin = windows["messageContent"]
    mwin.content.children = container # pyright: ignore
    app.layout.focus(container[-1])
    app._redraw()
    scrollTarget="messageContent"

def keybind_lore():
    kb = load_mouse_bindings()

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

    @kb.add("up", filter=Condition(lambda: scrollTarget != ""))
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

    @kb.add("down", filter=Condition(lambda: scrollTarget != ""))
    def sdown(e: KeyPressEvent):
        global focusingG
        st = scrollTarget+("" if scrollTarget == "guilds" else "_"+str(focusingG))
        if (i:=scrollCursorPos[st]+1) < len((win:=windows[scrollTarget].content.get_children())):
            win[i].style = tc.selectHighlight if scrollTarget != "messageContent" else tc.msgFocusHighlight # pyright: ignore
            win[i-1].style = "" # pyright: ignore
            scrollCursorPos[st]+=1
            app.layout.focus(win[i])
    
    @kb.add("enter", filter=Condition(lambda: mode != 1))
    async def click(e):
        global mode, scrollTarget, focusingG, focusingCh
        if mode == 2 and scrollTarget == "guilds":
            await render_channels(guilds[scrollCursorPos[scrollTarget]][1])
            windows[scrollTarget].content.get_children()[scrollCursorPos[scrollTarget]].style=""
            focusingG = guilds[scrollCursorPos[scrollTarget]][1]
        elif mode == 2 and scrollTarget == "channels":
            st = scrollTarget+("" if scrollTarget == "guilds" else "_"+str(focusingG))
            chInfo = channels[scrollCursorPos[st]]
            await render_messages(chInfo) # pyright: ignore
            focusingCh = chInfo.id
            mode = 2
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
        app.layout.focus(windows["messageInput"].body)
        mode = 1

    @kb.add("c-q")
    async def shut(e: KeyPressEvent):
        e.app.exit()
        await client.close()

    return kb
def _handle_exception(
    loop: asyncio.AbstractEventLoop, context: dict[str, Any]
) -> None:
    """
    Handler for event loop exceptions.
    This will print the exception, using run_in_terminal.
    """
    # For Python 2: we have to get traceback at this point, because
    # we're still in the 'except:' block of the event loop where the
    # traceback is still available. Moving this code in the
    # 'print_exception' coroutine will loose the exception.
    tb = help.get_traceback_from_context(context)
    formatted_tb = "".join(traceback.format_tb(tb))

    async def in_term() -> None:
        async with in_terminal():
            # Print output. Similar to 'loop.default_exception_handler',
            # but don't use logger. (This works better on Python 2.)
            exc: Exception = context.get("exception") # pyright: ignore
            print("\n----------------------------")
            print(formatted_tb)
            print("{0}: {1}".format(exc.__class__.__name__,exc))
            print("An error has occured. Find or report this issue on (h), I'll get right into it")

            await help.do_wait_for_enter("Press ENTER to continue...")

    asyncio.ensure_future(in_term())


def add_events(client:selfcord.Client):
    # load the main ui
    @client.event 
    async def on_ready():
        mainw = VSplit([
            windows["guilds"],
            windows["VerticalLine"],
            HSplit([
                Window(FormattedTextControl(""),height=2,style=tc.mainBg),
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
        loop.set_exception_handler(_handle_exception)
        #asyncio.ensure_future(typingAnim(),loop=loop)

        app.layout.container = mainw

        app.invalidate()

        render_guilds()

    # message events
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

    # typing
    @client.event 
    async def on_typing(ch: selfcord.TextChannel, usr: selfcord.Member, when: datetime):
        if ch.id == focusingCh:...

    return client

async def main():
    global windows, client, app
    conf = help.loadJson("config.json")
    windows = {
        "guilds": ScrollablePane(HSplit([Window()],style=tc.secondaryBg,width=12),show_scrollbar=False),
        "channels":ScrollablePane(HSplit([Window()],width=22,style=tc.channelListBg),show_scrollbar=False),
        "messageContent":ScrollablePane(HSplit([Window()],style=tc.mainBg), max_available_height=848940300),
        "forums":ScrollablePane(HSplit([Window()],style=tc.secondaryBg), max_available_height=848940300),
        "typing":VSplit([],height=1, style=tc.secondaryBg),
        "VerticalLine": Window(char=" ", style="class:line,vertical-line "+tc.secondaryBg, width=1),
        "messageInput": Frame(TextArea(text="bwhwhbsbe",height = 1,dont_extend_width=True),style=tc.channelListBg)
    }
    windows["messages"] = HSplit([windows["messageContent"], windows["messageInput"]], style = tc.mainBg) # pyright: ignore
    windows["typingList"] = Window(FormattedTextControl())
    
    kb = keybind_lore() 

    lay = Layout(HSplit([HSplit([Window(),Window(FormattedTextControl("\n\U000f066f"),align=WindowAlign.CENTER)]),Window(FormattedTextControl("This program requires Nerd Fonts to display icons.\nPlease install and use it as your ternimal font."), height=2, align=WindowAlign.CENTER)],style=tc.mainBg))
    app = Application(lay,full_screen=True,mouse_support=True, key_bindings=kb,style=style_from_pygments_cls(help.DisconsoleStyle))
    
    client = add_events(selfcord.Client())

    with patch_stdout(): await asyncio.wait([asyncio.create_task(client.start(token=conf["token"])), asyncio.create_task(app.run_async())])# pyright: ignore

asyncio.run(main())
