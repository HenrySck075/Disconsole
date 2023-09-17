import json, sys, os, platform, shutil, re, inspect
from types import TracebackType
from typing import Callable, ParamSpec, TypeVar, Any, Union, cast
import pygments, selfcord
from nullsafe import undefined,_
from ninety84 import DisconsoleToken, DshMarkdown, DisconsoleLexer, DisconsoleStyle, ThemeColors
MessageableChannel = Union[selfcord.TextChannel, selfcord.VoiceChannel, selfcord.StageChannel, selfcord.Thread, selfcord.DMChannel, selfcord.PartialMessageable, selfcord.GroupChannel]
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent as E
from prompt_toolkit.keys import Keys
from prompt_toolkit.shortcuts import PromptSession

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
P = ParamSpec("P")
RT = TypeVar("RT")
async def get_or_fetch(obj:Callable[P,RT], default = MISSING, *args:P.args, **kwargs:P.kwargs) -> RT: # pyright: ignore
    call = obj(*args,**kwargs) # pyright: ignore
    if call is None:
        attr = obj.__name__
        cls = [i for i in inspect.getmro(obj.im_class) if attr in i.__dict__][0]
        try:
            call = await getattr(cls, ("fetch_" if hasattr(cls,"fetch_"+attr) else "_fetch_")+attr)(*args,**kwargs)
        except (selfcord.HTTPException, ValueError):
            if default != MISSING:return default # pyright: ignore
            else: raise
    return call
async def format_message(client: selfcord.Client, msg: selfcord.Message):
    h = []
    for ttype, v in pygments.lex(msg.content, DisconsoleLexer()):
        if ttype == DisconsoleToken.MentionChannel:
            v = "# " + (await get_or_fetch(client.get_channel, id=int(v.replace("<#","").replace(">","")))).name # pyright: ignore
        if ttype == DisconsoleToken.MentionUser:
            if "<" in v:
                id = int(v.replace("<@","").replace(">",""))
                usr: selfcord.User | selfcord.Member = await (get_or_fetch(client.get_user, id=id) if type(msg.channel) == selfcord.DMChannel else get_or_fetch(msg.channel.guild.get_member, MISSING,id))
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
