
from dataclasses import dataclass
from textual.app import App
from textual.design import ColorSystem
from discord import Color
from types import MethodType

from textual.widget import Widget

@dataclass
class DarkThemeColors:
    primary = "#38393e"
    secondary = "#303136"
    guild = "#212226"
    accent = "#5865f2"
    select = "#42464e"
    highlight = "#3b3c41"

@dataclass
class LightThemeColors:
    primary = "#ffffff"
    secondary = "#ecedef"
    guild = "#e4e5e9"
    accent = "#74808d"
    select = "#d6d7dd"
    highlight = "#d6d7dd"
def color2hex(c: Color):
    return "#"+(hex(c.r)+hex(c.g)+hex(c.b)).replace("0x","")

def inject_output(colorSys: ColorSystem, css_classes: dict[str,str]):
    if css_classes != {}:
        setattr(colorSys, "generate_original", colorSys.generate)
        def generate(self):
            return self.generate_original() | css_classes # type: ignore
        colorSys.generate = MethodType(generate, colorSys)
    return colorSys
colorSys = {
    "dark": inject_output(ColorSystem(
        primary=DarkThemeColors.primary,
        secondary=DarkThemeColors.secondary,
        accent=DarkThemeColors.accent,
        dark=True
    ),{
        "guild": DarkThemeColors.guild,
        "highlight": DarkThemeColors.highlight,
        "select": DarkThemeColors.select
    }),
    "light": inject_output(ColorSystem(
        primary=LightThemeColors.primary,
        secondary=LightThemeColors.secondary,
        accent=LightThemeColors.accent,
    ),{
        "guild": LightThemeColors.guild,
        "highlight": LightThemeColors.highlight,
        "select": LightThemeColors.select
    })
}
def set_disconsole_css(app: App):
    return colorSys["dark" if app.dark else "light"].generate()
    
    

def set_theme_mode(app: App, darkMode: bool):
    app.console.push_theme

def getThemeColors(widget: Widget):
    return DarkThemeColors if widget.app.dark else LightThemeColors
