from datetime import datetime
from functools import partial
import traceback
import selfcord

from typing import Any, Callable, Coroutine
import asyncio, os

os.environ["PROMPT_TOOLKIT_COLOR_DEPTH"] = "DEPTH_24_BIT"
from nullsafe import undefined,_
import help 
zone = help.zone

try: import soundfile as sf, sounddevice as sd, numpy as np # audio stuff
except OSError as e:
    print(e,". Audio features won't be available")

from custom_widgets import RoundedFrame as Frame, FSProgressBar as ProgressBar
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.application import Application 
from prompt_toolkit.application.run_in_terminal import in_terminal
from prompt_toolkit.layout import Layout, Window, HSplit, VSplit, FormattedTextControl, WindowAlign, ScrollablePane
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.key_binding.bindings.mouse import load_mouse_bindings
from prompt_toolkit.styles.pygments import style_from_pygments_cls
from help import TypingList, DefaultDict, component

tc = help.ThemeColors()

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
guilds = []
channels = []
messages = []
forums = []
msgReplyMap = DefaultDict[int,int]({},0)


async def create_msg_window(i: selfcord.Message, notify_on_mention=False):
    return await component("Message", client=client, data=i, notify_on_mention=notify_on_mention)
def render_guilds():
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
                    ("bold: fg:"+await help.get_user_color(client, i.owner_id, channel.guild.id),(i.owner.name if i.owner is not None else "")+"  "),
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
    scrollCursorPos["messageContent_"+str(focusingCh)] = len(container)-1
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

    getst = lambda: scrollTarget+("" if scrollTarget == "guilds" else "_"+str(focusingG if scrollTarget=="channels" else focusingCh))
    def sup(amount: int, e):
        global focusingG
        st = getst()
        i=scrollCursorPos[st]-amount
        if i < 0: amount = scrollCursorPos[st]
        win = windows[scrollTarget].content.get_children()
        limbo = win[i] # type: Window
        un = win[i+amount]
        un.style = "" # pyright: ignore
        limbo.style = tc.selectHighlight if scrollTarget != "messageContent" else tc.msgFocusHighlight # pyright: ignore
        scrollCursorPos[st]-=amount
        app.layout.focus(limbo)
        app.invalidate()

    def sdown(amount:int, e: KeyPressEvent):
        global focusingG
        st = getst()
        i=scrollCursorPos[st]+amount
        win=windows[scrollTarget].content.get_children()
        if not i < len(win): amount = -(i-len(win))
        win[i].style = tc.selectHighlight if scrollTarget != "messageContent" else tc.msgFocusHighlight # pyright: ignore
        win[i-amount].style = "" # pyright: ignore
        scrollCursorPos[st]+=amount
        app.layout.focus(win[i])
        app.invalidate()

    kb.add("down", filter=Condition(lambda: scrollTarget != ""))(partial(sdown,1))
    kb.add("pagedown", filter=Condition(lambda: scrollTarget != ""))(partial(sdown,10))
    kb.add("up", filter=Condition(lambda: scrollTarget != ""))(partial(sup,1))
    kb.add("pageup", filter=Condition(lambda: scrollTarget != ""))(partial(sup,10))

    @kb.add("c-s-4")
    def refresh(e: KeyPressEvent):
        e.app.invalidate()
    
    @kb.add("enter", filter=Condition(lambda: mode != 1))
    async def click(e):
        global mode, scrollTarget, focusingG, focusingCh
        if mode == 2 and scrollTarget == "guilds":
            await render_channels(guilds[scrollCursorPos[scrollTarget]][1])
            windows[scrollTarget].content.get_children()[scrollCursorPos[scrollTarget]].style=""
            focusingG = guilds[scrollCursorPos[scrollTarget]][1]
        elif mode == 2 and scrollTarget == "channels":
            st = scrollTarget+"_"+str(focusingG)
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

    @kb.add("c-r", filter=Condition(lambda: mode == 2 and scrollTarget == "messageContent"))
    async def msg_reply(e):
        ctrl:FormattedTextControl = windows["msgReply"].content
        msg = messages[scrollCursorPos["messageContent_"+str(focusingCh)]]
        assert type(ctrl.text) == str, "nuh uh"
        ctrl.text = [ctrl.text[0], ("bold fg:"+await help.get_user_color(client, msg.author.id,focusingG))] # :traumatized_pero: # pyright: ignore
        msgReplyMap[focusingCh] = msg.id
        windows["messages"].children[1].children.insert(0,windows["msgReply"])

    # quit
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
        app.key_bindings = kb
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
            windows["messageContent"].content.children.append(h)
            lastUser = i.author.id
            app.invalidate()

            if scrollCursorPos["messageContent_"+str(focusingCh)] >= len(windows["messageContent"].content.children) - 10 :
                lastFocused = app.layout.current_window
                app.layout.focus(h)
                if not (scrollTarget == "messageContent" and mode == 2):
                    app.layout.focus(lastFocused)

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

KPECallable = Callable[[KeyPressEvent],None] | Callable[[KeyPressEvent],Coroutine[Any,Any,None]]
def multiline_input(on_escape: KPECallable, on_send: KPECallable):
    kb = KeyBindings()

    kb.add("enter")(on_send)
    kb.add("escape")(on_escape)

    return kb

async def main():
    global windows, client, app, kb
    conf = help.loadJson("config.json")
    kb = keybind_lore() 
    async def send_msg(e: KeyPressEvent):
        h = windows["messageInput"].body
        content = h.text
        st = "channels_"+str(focusingG)
        chinfo: selfcord.TextChannel = channels[scrollCursorPos[st]]
        h.text = ""
        app.layout.focus(windows["messageContent"].content.children[scrollCursorPos["messageContent_"+str(focusingCh)]])
        await chinfo.send(
            content,
            reference=selfcord.PartialMessage(channel=chinfo,id=msgReplyMap[chinfo.id]) if msgReplyMap[chinfo.id] != 0 else None # pyright: ignore
        ) 
        msgReplyMap[focusingCh] = 0
        c=windows["messages"].children[1].children
        if len(c)!=1:c.pop(0)

    windows = {
        "guilds": ScrollablePane(HSplit([Window()],style=tc.secondaryBg,width=12),show_scrollbar=False),
        "channels":ScrollablePane(HSplit([Window()],width=22,style=tc.channelListBg),show_scrollbar=False),
        "messageContent":ScrollablePane(HSplit([Window()],style=tc.mainBg), max_available_height=848940300),
        "forums":ScrollablePane(HSplit([Window()],style=tc.secondaryBg), max_available_height=848940300),
        "typing":VSplit([],height=1, style=tc.secondaryBg),
        "VerticalLine": Window(char=" ", style="class:line,vertical-line "+tc.secondaryBg, width=1),
        
    } | {
        "messageInput": Frame(TextArea(height = 1),style=tc.channelListBg,modal=True, key_bindings=multiline_input(kb.get_bindings_for_keys(("escape",))[0].call,send_msg)), # pyright: ignore
        "msgReply": Window(FormattedTextControl([("","Replying to ")],style=tc.mainBg),height=1)
    }
    windows["messages"] = HSplit([windows["messageContent"], HSplit([windows["messageInput"]])], style = tc.mainBg) # pyright: ignore
    windows["typingList"] = Window(FormattedTextControl())

    lay = Layout(HSplit([HSplit([Window(),Window(FormattedTextControl("\n\U000f066f"),align=WindowAlign.CENTER)]),Window(FormattedTextControl("Loading Disconsole"), height=2, align=WindowAlign.CENTER)],style=tc.mainBg))

    app = Application(lay,full_screen=True,mouse_support=True,style=style_from_pygments_cls(help.DisconsoleStyle))
    
    client = add_events(selfcord.Client())

    with patch_stdout(): await asyncio.wait([asyncio.create_task(client.start(token=conf["token"])), asyncio.create_task(app.run_async())])# pyright: ignore

asyncio.run(main())
