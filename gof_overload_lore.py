"Overloads for get_or_fetch function to satisfy type checkers"

import selfcord , selfcord.mixins
from typing import Literal, overload, Union
from MissingSentinel import MISSING
# guild object
@overload 
async def get_or_fetch(obj: selfcord.Guild, attr:Literal["member"], default=MISSING, *args, **kwargs) -> selfcord.Member:...

@overload 
async def get_or_fetch(obj: selfcord.Guild, attr:Literal["member_named"], default=MISSING, *args, **kwargs) -> selfcord.Member:...

@overload 
async def get_or_fetch(obj: selfcord.Guild, attr:Literal["channel"], default=MISSING, *args, **kwargs) -> Union[selfcord.TextChannel, selfcord.VoiceChannel, selfcord.ForumChannel, selfcord.StageChannel]:...

@overload 
async def get_or_fetch(obj: selfcord.Guild, attr:Literal["role"], default=MISSING, *args, **kwargs) -> selfcord.Role:...

@overload 
async def get_or_fetch(obj: selfcord.Guild, attr:Literal["thread"], default=MISSING, *args, **kwargs) -> selfcord.Thread:...

@overload 
async def get_or_fetch(obj: selfcord.Guild, attr:Literal["emoji"], default=MISSING, *args, **kwargs) -> selfcord.Emoji:...

@overload 
async def get_or_fetch(obj: selfcord.Guild, attr:Literal["stage_instance"], default=MISSING, *args, **kwargs) -> selfcord.StageInstance:...

@overload 
async def get_or_fetch(obj: selfcord.Guild, attr:Literal["scheduled_event"], default=MISSING, *args, **kwargs) -> selfcord.ScheduledEvent:...

@overload
async def get_or_fetch(obj: selfcord.Guild, attr:Literal["channel_or_thread"], default=MISSING, *args, **kwargs) -> Union[selfcord.TextChannel, selfcord.VoiceChannel, selfcord.ForumChannel, selfcord.StageChannel, selfcord.Thread]:...

# channels 

MessagableGuild = Union[selfcord.TextChannel, selfcord.VoiceChannel, selfcord.StageChannel]
@overload 
async def get_or_fetch(obj: Union[selfcord.TextChannel, selfcord.ForumChannel], attr:Literal["thread"], default=MISSING, *args, **kwargs) -> selfcord.Thread:...

@overload 
async def get_or_fetch(obj: MessagableGuild, attr:Literal["partial_message"], default=MISSING, *args, **kwargs) -> selfcord.PartialMessage:...

@overload 
async def get_or_fetch(obj: MessagableGuild, attr:Literal["message"], default=MISSING, *args, **kwargs) -> selfcord.Message:...

@overload 
async def get_or_fetch(obj: selfcord.StageChannel, attr:Literal["sinstance"], default=MISSING, *args, **kwargs) -> selfcord.StageInstance:...

# client user

@overload 
async def get_or_fetch(obj: selfcord.Client, attr:Literal["user"], default=MISSING, *args, **kwargs) -> selfcord.User:...

@overload 
async def get_or_fetch(obj: selfcord.Client, attr:Literal["channel"], default=MISSING, *args, **kwargs) -> Union[selfcord.TextChannel, selfcord.VoiceChannel, selfcord.ForumChannel, selfcord.StageChannel, selfcord.GroupChannel, selfcord.DMChannel, selfcord.Thread]:...

@overload 
async def get_or_fetch(obj: selfcord.Client, attr:Literal["role"], default=MISSING, *args, **kwargs) -> selfcord.Role:...

@overload 
async def get_or_fetch(obj: selfcord.Client, attr:Literal["stage_instance"], default=MISSING, *args, **kwargs) -> selfcord.StageInstance:...

@overload 
async def get_or_fetch(obj: selfcord.Client, attr:Literal["partial_messageable"], default=MISSING, *args, **kwargs) -> selfcord.PartialMessageable:...

@overload 
async def get_or_fetch(obj: selfcord.Client, attr:Literal["guild"], default=MISSING, *args, **kwargs) -> selfcord.Guild:...

async def get_or_fetch(obj: selfcord.mixins.Hashable, attr:str, default = MISSING, *args, **kwargs): # pyright: ignore
    "Get something from cache or fetch it if it doesn't exist or there's no get function named that"
    try: call = getattr(obj,"get_"+attr)(*args,**kwargs) # pyright: ignore
    except AttributeError: call = None
    if call is None:
        try:
            call = await getattr(obj, ("fetch_" if hasattr(obj,"fetch_"+attr) else "_fetch_")+attr)(*args,**kwargs)
        except (selfcord.HTTPException, ValueError):
            if default != MISSING:return default # pyright: ignore
            else: raise
        except AttributeError: raise AttributeError(f"what's my bro cooking there's nothing called {attr} in {obj}")
    return call
