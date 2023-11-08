from datetime import datetime
import json, sys, os, platform, shutil, re, inspect
from types import TracebackType
from typing import TypeVar, Any, Union, cast, Generic, TypedDict
from prompt_toolkit.layout import AnyContainer
import pygments, selfcord
from nullsafe import undefined,_
from ninety84 import DisconsoleToken, DshMarkdown, DisconsoleLexer, DisconsoleStyle, ThemeColors
MessageableChannel = Union[selfcord.TextChannel, selfcord.VoiceChannel, selfcord.StageChannel, selfcord.Thread, selfcord.DMChannel, selfcord.PartialMessageable, selfcord.GroupChannel]
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent as E
from prompt_toolkit.keys import Keys
from prompt_toolkit.shortcuts import PromptSession
from importlib import import_module
import composables
import dateutil.tz
zone = dateutil.tz.tzlocal()

def sizeof_fmt(num, suffix="B"):
    for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if abs(num) < 1000.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1000.0
    return f"{num:.1f}Y{suffix}"

def rf_relative_time(time:datetime):
    now = datetime.now(zone)
    diff = now - time.replace(tzinfo=zone)
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


system = platform.system 
if system == "Linux" and shutil.which("termux-change-repo") is not None:
    system = "Termux"
from MissingSentinel import MISSING

_KT = TypeVar("_KT",contravariant=True)
_VT = TypeVar("_VT",contravariant=True)
class TypingList(list):
    def __init__(self, *ok):
        super().__init__(*ok)

    def __setitem__(self, k: int, v: selfcord.User | selfcord.Member):
        list.__setitem__(self,k,v)

class DefaultDict(dict, Generic[_KT,_VT]):
    def __init__(self, map: dict[Any, Any] | None, default:_VT = None):
        super().__init__(map if map is not None else {})
        self.default_value = default

    def __getitem__(self, __key: _KT) -> _VT: # pyright: ignore
        try:
            return super().__getitem__(__key)
        except KeyError: 
            super().__setitem__(__key,self.default_value)
            return super().__getitem__(__key)

class a(TypedDict):
    guild: DefaultDict[int,str]
    dm: DefaultDict[int,str]

from functools import partial

def comprepl(self, funcName, *a, **k):
    return getattr(self.container, funcName)(*a,**k) #pyright: ignore
def replace(self,funcName):
    self.__dict__[funcName] = partial(comprepl,self,funcName)

compImpCache = {}
compMethodCache = DefaultDict({},[])
class AnyComponent:
    def __pt_container__(self): ...
    @classmethod
    async def create(cls, *args, **kwargs):...
async def component(name: str, componentsFolder="components", *createArgs, **createKwargs) -> AnyContainer:
    if name not in compImpCache:
        d = import_module(f".{componentsFolder}.{name}")
        compImpCache[name] = d
    else: d = compImpCache[name]
    if name not in compImpCache:
        di = composables.__dict__
        for i in di:
            if "__" not in i: setattr(d,i,di[i].export)
    c: AnyComponent = await d.Component.create(*createArgs, **createKwargs)
    if "__pt_container__" in c.__dir__():
        if name in compMethodCache:
            for i in compMethodCache[name]: replace(c,i)
        else:
            di = c.__dir__()
            for i in c.__pt_container__().__dir__():
                if "__" not in i and i not in di: 
                    replace(c,i)
                    compMethodCache[name].append(i)
    return c # pyright: ignore

userColorsCache:dict[int,a] = {}
from gof_overload_lore import get_or_fetch
async def get_user_color(client:selfcord.Client, user_id:int, guild_id:int, force=False) -> str:
    """
    NOTE: there's no fucking way discord gonna give us the color if it's from on message event

    :param force: Force fetching user color
    """
    global userColorsCache
    if user_id not in userColorsCache:
        userColorsCache[user_id] = {"dm":"", "guild":DefaultDict[int,str]({})} # pyright: ignore
    id = 0 
    root=DefaultDict[int,str]({}) # pyright: ignore
    if type(user_id) != int:
        raise TypeError("henry i thought pyright is that strict (`user` is not an integer)")
    if guild_id!=0:
        id = guild_id #pyright: ignore
        root = userColorsCache[user_id]["guild"]
    else:
        return "#95a5a6"

    if root[id] == None or force:
        if guild_id == 0: user = await get_or_fetch(client, "user",MISSING,user_id)
        else: 
            user = await get_or_fetch(await get_or_fetch(client, "guild", MISSING, guild_id), "member", MISSING, user_id)
            # except: return "#95a5a6"
        assert user is not None, "User does not exist"
        ret = root[id] = user.color.__str__()
        if ret == selfcord.Color(0).__str__(): ret = "#95a5a6"
        return ret
    else: return root[id]


# funky functions
async def do_wait_for_enter(wait_text: AnyFormattedText) -> None:
    """
    Create a sub application to wait for the enter key press.
    This has two advantages over using 'input'/'raw_input':
    - This will share the same input/output I/O.
    - This doesn't block the event loop.
    """

    key_bindings = KeyBindings()

    @key_bindings.add("enter")
    def _ok(event: E) -> None:
        event.app.exit()

    @key_bindings.add(Keys.Any)
    def _ignore(event: E) -> None:
        "Disallow typing."
        pass

    session: PromptSession[None] = PromptSession(
        message=wait_text, key_bindings=key_bindings
    )
    try:
        await session.app.run_async()
    except KeyboardInterrupt:
        pass  # Control-c pressed. Don't propagate this error.


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

async def format_message(client: selfcord.Client, msg: selfcord.Message):
    h = []
    for ttype, v in pygments.lex(msg.content, DisconsoleLexer()):
        if ttype == DisconsoleToken.MentionChannel:
            v = "# " + (await get_or_fetch(client,"channel", MISSING,int(v.replace("<#","").replace(">","")))).name # pyright: ignore
        if ttype == DisconsoleToken.MentionUser:
            if "<" in v:
                id = int(v.replace("<@","").replace(">",""))
                assert msg.channel.guild is not None, "shut"
                usr: selfcord.User | selfcord.Member = await (get_or_fetch(client,"user", MISSING, id) if type(msg.channel) == selfcord.DMChannel else get_or_fetch(msg.channel.guild, "member", MISSING,id))
                v = "@ " + usr.display_name
        if ttype == DisconsoleToken.MentionRole:
            id = int(v.replace("<@&","").replace(">",""))
            role = _(_(msg).guild).get_role(id) # pyright: ignore
            v = "@ "+role.name if role is not None else "deleted-role" # pyright: ignore
        if ttype == DshMarkdown.URL:
            v = re.findall(r"\[[^\[|\]]+\]\([a-zA-Z]*:\/\/(\S*)\)", v)[0][0]
        h.append((ttype,v))
    return h

def push_notification(title="Lorem ipsum", content="suichan pettan", type="DshMention"):
    "Create a notification (cross-platform)"

    match system:
        case "Windows": os.system(f'powershell ./windowsNotif.ps1 "{content}" "{title}" {type}')

        case "Termux": os.system(f'termux-notification -t "{title}" -c "{content}"')
