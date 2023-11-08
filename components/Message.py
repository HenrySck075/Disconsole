from datetime import datetime
from prompt_toolkit.widgets import Frame
import selfcord, help
from selfcord.errors import NotFound
from prompt_toolkit.layout import VSplit, Window, HSplit, FormattedTextControl, WindowAlign
from prompt_toolkit.formatted_text import PygmentsTokens, ANSI
import dateutil.tz
zone = dateutil.tz.tzlocal()
tc = help.ThemeColors()

class Component:
    def __init__(self) -> None:
        self.container: HSplit = HSplit([])

    @classmethod 
    async def create(cls, client: selfcord.Client, data: selfcord.Message, notify_on_mention=True):
        self = cls()
        def conditional_tuple(t:tuple[str,str],f:bool) -> tuple[str,str]:
            return t if f else ("","")
        def cond(h: list[tuple[tuple[str,str],bool]]):
            for i in h:
                if (x:=conditional_tuple(i[0],i[1])) != ("",""): return x 
            return ("","")
        assert data.channel.guild is not None

        data.content=data.content.strip("\n")
        if data.content != "":
            self.container=HSplit([
                Window(FormattedTextControl(PygmentsTokens(await help.format_message(client, data))),wrap_lines=True)
            ])
        else:
            self.container=HSplit([])
        for attach in data.attachments:
            self.container.children.append(await self.render_attachment(attach)) # pyright: ignore
        try: c = ("bold fg:"+await help.get_user_color(client, data.author.id,data.channel.guild.id),data.author.display_name+" ")
        except NotFound: c = ("bold", "Deleted User ")
        w = Window(FormattedTextControl([
            c,
            cond([((tc.accent,"BOT"),data.author.bot),((tc.accent,"\U000f012c BOT"),data.author.bot and data.author.public_flags.verified_bot),((tc.accent,"SYSTEM"),data.author.system)]),
            ("fg:gray",self.rm_message_timestamp(data.created_at))
        ]),height=1)
        self.container.children.insert(0, w)
        if (msgref:=data.reference) is not None:
            msg = msgref.resolved
            # 1: conditional container is bloatware
            # 2: pyright will shout at me for None
            if type(msg) == selfcord.Message:
                self.container.children.insert(0, Window(FormattedTextControl([
                    ("","\U000f0772"),
                    ("bold fg:"+await help.get_user_color(client, msg.author.id,data.channel.guild.id), msg.author.display_name+" "),
                    ("fg:gray",msg.content)
                ]),height=1))
            else:
                self.container.children.insert(0, Window(FormattedTextControl([
                    ("","\U000f0772"),
                    ("italic fg:gray","Cannot load the message." if type(msg) == None else "Original message was deleted.")
                ])))
        if client.user in data.mentions:
            self.container.style = tc.msgMentionHighlight
            if notify_on_mention: help.push_notification(data.channel.guild.name + " #"+data.channel.name, data.content) # pyright: ignore
        self.container.children.append(Window(FormattedTextControl(" ",focusable=True)))
        return self

    async def render_attachment(self, attach: selfcord.Attachment):
        assert attach.content_type is not None
        if "text/" in attach.content_type:
            return Frame(
                HSplit([
                    Window(FormattedTextControl((await attach.read()).decode()),height=6),
                    Window(FormattedTextControl([
                        ("bold", attach.filename),
                        ("fg:gray", help.sizeof_fmt(attach.size))
                    ]),align=WindowAlign.RIGHT)
                ],style=tc.channelListBg),
                style=tc.channelListBg+" "+tc.secondaryBg.replace("bg","fg")
            )
        if "audio/" in attach.content_type:
            assert type(attach.duration) == float
            return Frame(
                HSplit([
                    Window(FormattedTextControl([
                        (tc.accent, "\uf1c7"),
                        (tc.url, attach.filename),
                        ("fg:gray", help.sizeof_fmt(attach.size))
                    ])),
                    VSplit([
                        Window(FormattedTextControl("\U000f040a",style="fg:#A0A0A1")),
                        Window(FormattedTextControl("0:00/"+str(attach.duration))),
                        # ProgressBar(attach.duration,style=tc.accent),
                        Window(FormattedTextControl("\ue638",style="fg:#A0A0A1")),
                    ],style=tc.secondaryBg)
                ],style=tc.channelListBg)
            )
        if "image/" in attach.content_type and "gif" not in attach.content_type:
            return Window(FormattedTextControl("\n"+useANSI(await attach.read())))# pyright: ignore
        else: return Window(FormattedTextControl("\U000f0066 "+attach.url,tc.url))

    def rm_message_timestamp(self, date: datetime):
        now = datetime.now(zone)
        diff = now - date.replace(tzinfo=zone)
        if diff.days == 0: 
            return date.strftime("Today at %I:%M %p")
        if diff.days == 1:
            return date.strftime("Yesterday at %I:%M %p")
        else:
            return date.strftime("%d/%m/%Y %I:%M %p")

    def __pt_container__(self):
        return self.container


