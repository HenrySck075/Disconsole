from collections.abc import Awaitable, Callable, Coroutine
import logging
from typing import TYPE_CHECKING, Any, Literal, ParamSpec, overload
from discord import Client
import sqlite3

from discord.abc import T

_log = logging.getLogger("discord")

Events = Literal[
    "automod_rule_create",
    "automod_rule_update",
    "automod_rule_delete",
    "automod_action",

    "guild_channel_create",
    "guild_channel_delete",
    "guild_channel_update",
    "guild_channel_pins_update",

    "private_channel_create",
    "private_channel_delete",
    "private_channel_update",
    "private_channel_pins_update",

    "group_join",
    "group_remove",

    "typing",

    "connect",
    "disconnect",

    "ready",
    "resume",

    "settings_update",
    "guild_settings_update",
    "required_action_update",
    "user_feature_ack",

    "payment_sources_update",
    "subscriptions_update",
    "payment_client_add",
    "payment_update",
    "premium_guild_subscription_slot_create",
    "premium_guild_subscription_slot_update",
    "billing_popup_bridge_callback",

    "library_application_update",
    "achievement_update",
    "entitlement_create"
    "entitlement_update"
    "gift_create",
    "gift_update",

    "connections_update",
    "connection_create",
    "connection_update",
    "connection_link_callback",
    
    "relationship_add",
    "relationship_remove",
    "relationship_update",
    "friend_suggestion_add",
    "friend_suggestion_remove",
    "raw_friend_suggestion_remove",

    "note_update",

    "oauth2_token_revoke",

    "call_create",
    "call_delete",
    "call_update",

    "guild_available",
    "guild_unavailable",
    "guild_join",
    "guild_remove",
    "guild_update",
    "guild_emojis_update",
    "guild_stickers_update",
    "application_command_index_update",
    "audit_log_entry_create",
    "invite_create",
    "invite_delete",
    "guild_feature_ack",

    "integration_create",
    "integration_update",
    "guild_integrations_create",
    "webhooks_update",
    "raw_integration_delete",

    "interaction",
    "interaction_finish",
    "modal",

    "member_join",
    "member_remove",
    "raw_member_remove",
    "member_update",
    "user_update",
    "member_ban",
    "member_unban",
    "presence_update",
    "raw_member_list_update",

    "message",
    "message_edit",
    "message_delete",
    "bulk_message_delete",
    "message_ack",
    "raw_message_edit",
    "raw_message_delete",
    "raw_bulk_message_delete",
    "raw_message_ack",
    "recent_mention_delete",
    "raw_recent_mention_delete",

    "reaction_add",
    "reaction_remove",
    "reaction_clear",
    "reaction_clear_emoji",
    "raw_reaction_add",
    "raw_reaction_remove",
    "raw_reaction_clear",
    "raw_reaction_clear_emoji",

    "guild_role_create",
    "guild_role_delete",
    "guild_role_update",

    "scheduled_event_create",
    "scheduled_event_delete",
    "scheduled_event_update" 
]

if TYPE_CHECKING:
    from discord import Guild
    Coro = Coroutine[Any, Any, None]

    on_general_guild_status = Callable[[Guild],Coro]
    on_basic_events = Callable[[],Coro]

P = ParamSpec("P")
class Client2(Client):

    def __init__(self, **options) -> None:
        super().__init__(**options)
        self._events: dict[str, list[Callable[..., Coroutine[Any, Any, None]]]] = {}
        """
        self.db = sqlite3.connect("db.db")
        self.cur = self.db.cursor()

        self.cur.execute("CREATE TABLE IF NOT EXISTS unread_channels (id INT PRIMARY KEY NOT NULL, ts ID NOT NULL)")
        # self.cur.execute("CREATE TABLE IF NOT EXISTS user_settings (id INT PRIMARY KEY NOT NULL, ts ID NOT NULL)")
        """

    def add_listener(
        self, 
        event_name: Events,
        listener: Callable[..., Coroutine[Any, Any, None]]
    ):
        if event_name not in self._events:
            self._events[event_name] = []
        self._events[event_name].append(listener)

    def remove_listener(self, event_name: Events,listener: Callable[..., Coroutine[Any, Any, None]]):
        self._events[event_name].remove(listener)

    def dispatch(self, event: str, /, *args: Any, **kwargs: Any) -> None:
        _log.debug('Dispatching event %s.', event)
        method = 'on_' + event

        listeners = self._listeners.get(event)
        if listeners:
            removed = []
            for i, (future, condition) in enumerate(listeners):
                if future.cancelled():
                    removed.append(i)
                    continue

                try:
                    result = condition(*args)
                except Exception as exc:
                    future.set_exception(exc)
                    removed.append(i)
                else:
                    if result:
                        if len(args) == 0:
                            future.set_result(None)
                        elif len(args) == 1:
                            future.set_result(args[0])
                        else:
                            future.set_result(args)
                        removed.append(i)

            if len(removed) == len(listeners):
                self._listeners.pop(event)
            else:
                for idx in reversed(removed):
                    del listeners[idx]

        try:
            coros = self._events[method] 
        except KeyError:
            pass
        else:
            for coro in coros: self._schedule_event(coro, method, *args, **kwargs)



    async def get_or_fetch(self, obj: object, fetch_method: Callable[P, Awaitable[T]], *args, **kwargs) -> T:
        try:
            get_method: Callable[P,T|None] = getattr(obj, fetch_method.__name__.replace("fetch","get"))
            r = get_method(*args, **kwargs)
            if r != None: 
                return r
        except AttributeError | ValueError:
            pass 
        return await fetch_method(*args, **kwargs)
        

