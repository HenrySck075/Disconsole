import json, sys, os, platform, shutil
import re
from types import TracebackType
from typing import TypeVar, Any, Union, cast
import pygments, selfcord
from nullsafe import undefined,_
from ninety84 import DisconsoleToken, DshMarkdown, DisconsoleLexer, DisconsoleStyle, ThemeColors
MessageableChannel = Union[selfcord.TextChannel, selfcord.VoiceChannel, selfcord.StageChannel, selfcord.Thread, selfcord.DMChannel, selfcord.PartialMessageable, selfcord.GroupChannel]
from prompt_toolkit.layout import FloatContainer, Float, Container, Window

system = platform.system 
if system == "Linux" and shutil.which("termux-change-repo") is not None:
    system = "Termux"

class MissingSentinel:
    def __repr__(self):
        return "..."
    def __str__(self) -> str:
        return self.__repr__()
MISSING = MissingSentinel()
# funky functions
def get_traceback_from_context(context: dict[str, Any]) -> TracebackType | None:
    """
    Get the traceback object from the context.
    """
    exception = context.get("exception")
    if exception:
        if hasattr(exception, "__traceback__"):
            return cast(TracebackType, exception.__traceback__)
        else:
            # call_exception_handler() is usually called indirectly
            # from an except block. If it's not the case, the traceback
            # is undefined...
            return sys.exc_info()[2]

    return None
def loadJson(filename) -> dict | list: 
    return json.load(open(filename, "r"))

def addattr(o,**h):
    for i in h.keys():
        setattr(o,i,h[i])
    return o

def runmethod(iter:list, methods:list):
    for i in iter:
        h = {"i":i}
        [exec(f"i.{m}",h) for m in methods]

h = TypeVar("h", covariant=True, bound=dict)

def modifyValue(dic:h, key, stuff) -> h:
    if key != "":
        dic[key] = stuff(dic[key])
    return dic

async def get_or_fetch(obj, attr, id, default = MISSING, **kwargs) -> Any:
    call = getattr(obj,"get_"+attr)(id, **kwargs)
    if call is None:
        try:
            call = await getattr(obj, ("fetch_" if hasattr(obj,"fetch_"+attr) else "_fetch_")+attr)(id, **kwargs)
        except (selfcord.HTTPException, ValueError):
            if default != MISSING:return default
            else: raise
    return call

async def format_message(client: selfcord.Client, msg: selfcord.Message):
    h = []
    for ttype, v in pygments.lex(msg.content, DisconsoleLexer()):
        if ttype == DisconsoleToken.MentionChannel:
            v = "# " + (await get_or_fetch(client, "channel", int(v.replace("<#","").replace(">","")))).name
        if ttype == DisconsoleToken.MentionUser:
            if "<" in v:
                id = int(v.replace("<@","").replace(">",""))
                usr: selfcord.User | selfcord.Member = await (get_or_fetch(client, "user", id) if type(msg.channel) == selfcord.DMChannel else get_or_fetch(msg.channel.guild, "member", id))
                v = "@ " + usr.display_name
        if ttype == DisconsoleToken.MentionRole:
            id = int(v.replace("<@&","").replace(">",""))
            role = _(_(msg).guild).get_role(id) # pyright: ignore
            v = "@ "+role.name if role is not None else "deleted-role" # pyright: ignore
        if ttype == DshMarkdown.URL:
            v = re.findall(r"\[[^\[|\]]+\]\([a-zA-Z]*:\/\/(\S*)\)", v)[0][0]
        h.append((ttype,v))
    return h

def box_container(container:Container, tl="┎",tr="┒",bl="┖",br="┚",lr="┃",tb="━"): 
    nein = {"width":1,"height":1}
    n = nein|{"top":-1}
    m = nein|{"bottom":-1}
    return FloatContainer(
        container,
        [
            #side
            Float(Window(style="class:border",char=lr),0,None,0,-1,1),
            Float(Window(style="class:border",char=lr),0,-1,0,None,1),
            Float(Window(style="class:border",char=tb),-1,0,None,0,0,1),
            Float(Window(style="class:border",char=tb),None,0,-1,0,0,1),

            #corn 
            Float(Window(style="class:border",char=tl),top=-1,**n),
            Float(Window(style="class:border",char=tr),top=-1,**m),
            Float(Window(style="class:border",char=bl),bottom=-1,**n),
            Float(Window(style="class:border",char=br),bottom=-1,**m)
        ]
    )

def push_notification(title="Lorem ipsum", content="suichan pettan", type="DshMention"):
    "Create a notification (cross-platform)"

    match system:
        case "Windows": os.system(f'powershell ./windowsNotif.ps1 "{content}" "{title}" {type}')

        case "Termux": os.system(f'termux-notification -t "{title}" -c "{content}"')
