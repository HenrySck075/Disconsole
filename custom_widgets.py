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

class WindowWithUsrdat(Window):
    def __init__(self, data, *args, **kwargs):
        """
        Container that holds a control (with user data).
        To add data to a _Split, choose a focusable container and let it hold the data (current Disconsole implementaion idk how you will do that).

        :param data: anything
        :param content: :class:`.UIControl` instance.
        :param width: :class:`.Dimension` instance or callable.
        :param height: :class:`.Dimension` instance or callable.
        :param z_index: When specified, this can be used to bring element in front
            of floating elements.
        :param dont_extend_width: When `True`, don't take up more width then the
                                  preferred width reported by the control.
        :param dont_extend_height: When `True`, don't take up more width then the
                                   preferred height reported by the control.
        :param ignore_content_width: A `bool` or :class:`.Filter` instance. Ignore
            the :class:`.UIContent` width when calculating the dimensions.
        :param ignore_content_height: A `bool` or :class:`.Filter` instance. Ignore
            the :class:`.UIContent` height when calculating the dimensions.
        :param left_margins: A list of :class:`.Margin` instance to be displayed on
            the left. For instance: :class:`~prompt_toolkit.layout.NumberedMargin`
            can be one of them in order to show line numbers.
        :param right_margins: Like `left_margins`, but on the other side.
        :param scroll_offsets: :class:`.ScrollOffsets` instance, representing the
            preferred amount of lines/columns to be always visible before/after the
            cursor. When both top and bottom are a very high number, the cursor
            will be centered vertically most of the time.
        :param allow_scroll_beyond_bottom: A `bool` or
            :class:`.Filter` instance. When True, allow scrolling so far, that the
            top part of the content is not visible anymore, while there is still
            empty space available at the bottom of the window. In the Vi editor for
            instance, this is possible. You will see tildes while the top part of
            the body is hidden.
        :param wrap_lines: A `bool` or :class:`.Filter` instance. When True, don't
            scroll horizontally, but wrap lines instead.
        :param get_vertical_scroll: Callable that takes this window
            instance as input and returns a preferred vertical scroll.
            (When this is `None`, the scroll is only determined by the last and
            current cursor position.)
        :param get_horizontal_scroll: Callable that takes this window
            instance as input and returns a preferred vertical scroll.
        :param always_hide_cursor: A `bool` or
            :class:`.Filter` instance. When True, never display the cursor, even
            when the user control specifies a cursor position.
        :param cursorline: A `bool` or :class:`.Filter` instance. When True,
            display a cursorline.
        :param cursorcolumn: A `bool` or :class:`.Filter` instance. When True,
            display a cursorcolumn.
        :param colorcolumns: A list of :class:`.ColorColumn` instances that
            describe the columns to be highlighted, or a callable that returns such
            a list.
        :param align: :class:`.WindowAlign` value or callable that returns an
            :class:`.WindowAlign` value. alignment of content.
        :param style: A style string. Style to be applied to all the cells in this
            window. (This can be a callable that returns a string.)
        :param char: (string) Character to be used for filling the background. This
            can also be a callable that returns a character.
        :param get_line_prefix: None or a callable that returns formatted text to
            be inserted before a line. It takes a line number (int) and a
            wrap_count and returns formatted text. This can be used for
            implementation of line continuations, things like Vim "breakindent" and
            so on.
        """

        super().__init__(*args,**kwargs)
        self.data = data

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


