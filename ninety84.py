from pygments.lexer import RegexLexer
from pygments.style import Style
from pygments.token import Token
DisconsoleToken = Token.Disconsole
DshMarkdown = DisconsoleToken.Markdown 
import re


class ThemeColors:
    focusHighlight = "bg:#35373C"
    mainBg = "bg:#313338"
    channelListBg = "bg:#2B2D31"
    secondaryBg = "bg:#232428"
    selectHighlight = "bg:#404249"
    msgFocusHighlight = "bg:#2F3238"
    msgMentionHighlight = "bg:#444037"
    url = "fg:#00A8FC"
    mentionTextHighlight = "bg:#4e4e74"
tc = ThemeColors()
escs = re.escape("*")
print(escs)

class DisconsoleLexer(RegexLexer):
    tokens = {
        "root": [
            (r'[a-zA-Z]*:\/\/(\S*)', DisconsoleToken.URL),
            (r'<#(\d+)>', DisconsoleToken.MentionChannel),
            (r'<@(\d+)>|@(everyone|here)', DisconsoleToken.MentionUser),
            (r'<@&(\d+)>', DisconsoleToken.MentionRole),


            # markdown 
            ("(\\*|\\_){1}(^[\\n|\\*]$1{1})", DshMarkdown.Italic),
            ("(\\*){2}(^[\\n|\\*]$1{2})", DshMarkdown.Bold),
            (r"(\*){3}+(\S+)(\*){3}+", DshMarkdown.ItaBold),
            ("(\\_){2}(^[\\n|\\_]$1{2})", DshMarkdown.Underline),
            (r"(\_){3}+(\S+)(\_){3}+", DshMarkdown.UnderItalic),
            (r'\`([^(`|\n)]+)`', DshMarkdown.InlineCodeblock),
            (r'`{3}\n(.+)\n`{3}', DshMarkdown.MultilineCodeblock),
            (r'\[[^\[|\]]+\]\([a-zA-Z]*:\/\/(\S*)\)', DshMarkdown.URL)
        ]
    }

class DisconsoleStyle(Style):
    styles = {
        DisconsoleToken.URL: tc.url.replace("fg:",""),
        DisconsoleToken.MentionChannel: tc.mentionTextHighlight,
        DisconsoleToken.MentionUser: tc.mentionTextHighlight,

        DshMarkdown.Italic: "italic",
        DshMarkdown.Bold: "bold",
        DshMarkdown.ItaBold: "italic bold",
        DshMarkdown.Underline: "underline",
        DshMarkdown.UnderItalic: "underline italic",
        DshMarkdown.InlineCodeblock: tc.channelListBg,
        DshMarkdown.MultilineCodeblock: tc.channelListBg,
        DshMarkdown.URL: tc.url.replace("fg:",""),
    }


