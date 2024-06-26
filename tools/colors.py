
from dataclasses import dataclass

from discord import Color


@dataclass
class ThemeColors:
    primary = "#38393e"
    secondary = "#303136"
    guild = "#212226"
    accent = "#5865f2"


def color2hex(c: Color):
    return "#"+(hex(c.r)+hex(c.g)+hex(c.b)).replace("0x","")
