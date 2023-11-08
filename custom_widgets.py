from prompt_toolkit.widgets import Label
from prompt_toolkit.layout import DynamicContainer, AnyDimension, AnyContainer, FormattedTextControl, Window, HSplit, VSplit, ConditionalContainer, Container
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import Template, AnyFormattedText
from functools import partial

class FSProgressBar(Window):
    def __init__(self, total:float, *args, **kwargs):
        super().__init__(FormattedTextControl(""),*args,**kwargs|{"height":1})
        self.total = total
        self.progress = 0
        self._ratio = 0

    def update_progress(self, h: float):
        assert h <= self.total, "dude you're high or smth (progress is higher than the given `total` value)"
        self.progress = h
        self.ratio = self.total/h

    @property
    def ratio(self): return self._ratio
    
    @ratio.setter 
    def ratio(self, v:float):
        self._ratio = v
        self.content = FormattedTextControl("\u25a0"*self.preferred_width(self.width).preferred)

class UserDataContainer:
    def __init__(self, data, container: Container):
        """
        Container that holds a control (with user data).
        To add data to a _Split, choose a focusable container and let it hold the data (current Disconsole implementaion idk how you will do that).

        :param data: anything
        :param 
        """

        super().__init__()
        self.data = data
        self.container = container

    def __pt_container__(self): return self.container

class RoundedFrame:
    """
    Draw a border around any container, optionally with a title text.

    Changing the title and body of the frame is possible at runtime by
    assigning to the `body` and `title` attributes of this class.

    :param body: Another container object.
    :param title: Text to be displayed in the top of the frame (can be formatted text).
    :param style: Style string to be applied to this widget.
    """

    def __init__(
        self,
        body: AnyContainer,
        title: AnyFormattedText = "",
        style: str = "",
        width: AnyDimension = None,
        height: AnyDimension = None,
        key_bindings: KeyBindings | None = None,
        modal: bool = False,
    ) -> None:
        self.title = title
        self.body = body

        fill = partial(Window, style="class:frame.border")
        style = "class:frame " + style

        top_row_with_title = VSplit(
            [
                fill(width=1, height=1, char="\u256d"),
                fill(char="|"),
                fill(width=1, height=1, char="\u2500"),
                # Notice: we use `Template` here, because `self.title` can be an
                # `HTML` object for instance.
                Label(
                    lambda: Template(" {} ").format(self.title),
                    style="class:frame.label",
                    dont_extend_width=True,
                ),
                fill(width=1, height=1, char="\u2500"),
                fill(char="|"),
                fill(width=1, height=1, char="\u256e"),
            ],
            height=1,
        )

        top_row_without_title = VSplit(
            [
                fill(width=1, height=1, char="\u256d"),
                fill(char="\u2500"),
                fill(width=1, height=1, char="\u256e"),
            ],
            height=1,
        )

        @Condition
        def has_title() -> bool:
            return bool(self.title)

        self.container = HSplit(
            [
                ConditionalContainer(content=top_row_with_title, filter=has_title),
                ConditionalContainer(content=top_row_without_title, filter=~has_title),
                VSplit(
                    [
                        fill(width=1, char="\u2502"),
                        DynamicContainer(lambda: self.body),
                        fill(width=1, char="\u2502"),
                        # Padding is required to make sure that if the content is
                        # too small, the right frame border is still aligned.
                    ],
                    padding=0,
                ),
                VSplit(
                    [
                        fill(width=1, height=1, char="\u2570"),
                        fill(char="\u2500"),
                        fill(width=1, height=1, char="\u256f"),
                    ],
                    # specifying height here will increase the rendering speed.
                    height=1,
                ),
            ],
            width=width,
            height=height,
            style=style,
            key_bindings=key_bindings,
            modal=modal,
        )

    def __pt_container__(self) -> Container:
        return self.container


