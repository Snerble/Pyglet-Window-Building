from pyglet import gl, graphics, media, text, sprite
from math import sin, cos, pi, radians
from tools import runAsNewThread
from interface.gltools import *

class Constraint:
    def getValue(self):
        raise NotImplementedError()
    def setValue(self, value):
        raise NotImplementedError()
    
    def __int__(self):
        return int(self.getValue())
    def __float__(self):
        return float(self.getValue())

class AbsoluteConstraint(Constraint):
    def __init__(self, value : (int, float)):
        self.__value = value
    
    def getValue(self):
        return self.__value

    def setValue(self, value : (int, float)):
        self.__value = value
    
class RelativeConstraint(Constraint):
    def __init__(self, limit, offset=0):
        assert limit.__class__.__name__ == "function"
        self.__limit = limit
        self.__offset = offset

    def getValue(self):
        return self.__limit() + self.offset
    
    def setValue(self, limit, offset=None):
        assert limit.__class__.__name__ == "function"
        self.__limit = limit
        if offset: self.offset = offset

    @property
    def offset(self):
        return self.__offset
    @offset.setter
    def offset(self, offset: (int, float)):
        self.__offset = offset
    
    @staticmethod
    def toTopOf(component: 'Component', offset=0):
        return RelativeConstraint(lambda : component.y, offset)
    @staticmethod
    def toRightOf(component: 'Component', offset=0):
        return RelativeConstraint(lambda : component.x + component.width, offset)
    @staticmethod
    def toLeftOf(component: 'Component', offset=0):
        return RelativeConstraint(lambda : component.x, offset)
    @staticmethod
    def toBottomOf(component: 'Component', offset=0):
        return RelativeConstraint(lambda : component.y + component.height, offset)

class Component:
    def __init__(self, x=0, y=0, width=0, height=0, **kwargs):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        def set_state():
            gl.glPushMatrix()
            gl.glTranslatef(self.x, self.y, 0)
        
        def unset_state():
            gl.glPopMatrix()

        self._group = graphics.Group(kwargs.get("group"))
        self._group.set_state = set_state
        self._group.unset_state = unset_state
        self.background = graphics.OrderedGroup(0, self._group)
        self.foreground = graphics.OrderedGroup(1, self._group)

    def draw(self):
        raise NotImplementedError()

    def update(self, *args, **kwargs):
        raise NotImplementedError()
    
    def __call__(self, *args, **kwargs):
        self.draw()
        return 0

    def set_handlers(self, window):
        raise NotImplementedError()

    def setPosition(self, x, y):
        self.x = x
        self.y = y
    
    def move(self, x, y):
        self.x += x
        self.y += y

    @property
    def x(self):
        return int(self.__x) if type(self.__x) == int else float(self.__x)
    @x.setter
    def x(self, x):
        assert type(x) in (int, float) or issubclass(type(x), Constraint)
        self.__x = x

    @property
    def y(self):
        return int(self.__y) if type(self.__y) == int else float(self.__y)
    @y.setter
    def y(self, y):
        assert type(y) in (int, float) or issubclass(type(y), Constraint)
        self.__y = y
    
    @property
    def width(self):
        return int(self.__width) if type(self.__width) == int else float(self.__width)
    @width.setter
    def width(self, width):
        assert type(width) in (int, float) and width >= 0 or issubclass(type(width), Constraint)
        self.__width = width
        
    @property
    def height(self):
        return int(self.__height) if type(self.__height) == int else float(self.__height)
    @height.setter
    def height(self, height):
        assert type(height) in (int, float) and height >= 0 or issubclass(type(height), Constraint)
        self.__height = height

    def contains(self, x, y):
        return x >= self.x and x < self.x + self.width and y >= self.y and y < self.y + self.width

class Polygon(Component):
    def __init__(self, vertices: list, colors=None, x=0, y=0):
        assert len(vertices) > 0
        assert colors == None or len(colors) == 1 or len(colors) == len(vertices)
        
        width, height = (0,0)
        for vx, vy in vertices:
            if vx > width: width = vx
            if vy > height: height = vy
        super(Polygon, self).__init__(x, y, width, height)
        self._vertices = vertices
        self._colors = colors
    
    def draw(self):
        multiColor = True
        if self._colors:
            if type(self._colors) != list:
                multiColor = False
                gl.glColor3f(*(c / 255 for c in self._colors))
        i = 0
        gl.glTranslatef(self.x, self.y, 0)
        gl.glBegin(gl.GL_POLYGON)
        while i < len(self._vertices):
            if self._colors and multiColor:
                gl.glColor3f(*(c / 255 for c in self._colors[i]))
            gl.glVertex2f(*self._vertices[i])
            i+=1
        gl.glEnd()
        gl.glTranslatef(-self.x, -self.y, 0)

class TextBox(Component):
    def __init__(self, x, y, width, height, radius=0, **kwargs):
        super(TextBox, self).__init__(x, y, width, height)
        self.__batch = kwargs.get("batch")
        self.__group = kwargs.get("group")
        
        if type(radius) in (int, float):
            radius = (radius, radius, radius, radius)
        self.radius = radius
        
        _text = kwargs.get("text", "")
        self.color = kwargs.get("color", (255,255,255,255))
        font_color = kwargs.get("font_color", (0,0,0,255))
        font_name = kwargs.get("font_name", "Sans-Serif")
        font_size = kwargs.get("font_size", 16)
        italic = kwargs.get("italic", False)
        bold = kwargs.get("bold", False)
        self.padding = dict(
            left=kwargs.get("padding_left", kwargs.get("padding", 0)),
            right=kwargs.get("padding_right", kwargs.get("padding", 0)),
            top=kwargs.get("padding_top", kwargs.get("padding", 0)),
            bottom=kwargs.get("padding_bottom", kwargs.get("padding", 0))
        )
        placeholder = kwargs.get("placeholder", "")

        self.document = text.document.FormattedDocument(_text if len(_text) != 0 else " ")
        self.document.set_style(0, max(1, len(self.document.text)), dict(
            font_name=font_name,
            font_size=font_size,
            italic=italic,
            bold=bold,
            color=font_color
        ))
        self.document.text = _text

        def set_state():
            self.layout.x, self.layout.y = self.x + self.padding["left"], self.y + self.padding["top"]
            self.layout.width, self.layout.height = self.width - self.padding["left"] - self.padding["right"], self.height - self.padding["top"] - self.padding["bottom"]
            if (len(self.layout.document.text) != 0): self.placeholder.color = (0,0,0,0)
            else: self.placeholder.color = (*(x + 85 * (1 if x < 128 else -1) for x in self.color[:3]), self.color[3])
        self.foreground.set_state = set_state

        self.layout = text.layout.IncrementalTextLayout(self.document, self.width, self.height, batch=self.__batch, wrap_lines=False)
        self.layout.content_valign = "center"
        self.caret = text.caret.Caret(self.layout, batch=self.__batch, color=font_color[:3])

        self.placeholder = text.Label(placeholder if len(placeholder) != 0 else " ",
                        font_name=font_name,
                        font_size=font_size,
                        italic=italic,
                        bold=bold,
                        x=self.padding["left"],
                        y=self.padding["top"],
                        width=self.width-self.padding["right"]-self.padding["left"],
                        height=self.height-self.padding["bottom"]-self.padding["top"],
                        anchor_y="bottom",
                        batch=self.__batch,
                        group=self.foreground)
        self.placeholder.content_valign = "center"

        def set_state1():
            gl.glPushAttrib(gl.GL_CURRENT_BIT)
            gl.glColor4f(*(x / 255 for x in self.color))
        def unset_state1():
            gl.glPopAttrib()
        self.background.set_state, self.background.unset_state = set_state1, unset_state1

        self.shape = createRoundRect(0, 0, self.width, self.height, self.radius, batch=self.__batch, group=self.background)
        self.actions = list()

    def activate(self):
        for act in self.actions:
            act(self.layout.document.text)

    def on_text(self, text):
        if text == '\r':
            self.activate()
            return
        self.caret.on_text(text)

    def set_handlers(self, window):
        window.set_handlers(self.caret, on_text=self.on_text)

class Button(Component):
    def __init__(self, x, y, width, height, radius=0, **kwargs):
        super(Button, self).__init__(x, y, width, height)
        self.__batch = kwargs.get("batch")
        self.__group = kwargs.get("group")

        _text = kwargs.get("text")
        self.tooltip = kwargs.get("tooltip")
        self.color = kwargs.get("color", (255,255,255,255))
        font_color = kwargs.get("font_color", (0,0,0,255))
        font_name = kwargs.get("font_name", "Sans-Serif")
        font_size = kwargs.get("font_size", 16)
        italic = kwargs.get("italic", False)
        bold = kwargs.get("blold", False)
        image = kwargs.get("image")

        if image:
            self.media = sprite.Sprite()

        self.text = text.Label(
            text=_text,
            font_name=font_name,
            font_size=font_size,
            color=font_color,
            italic=italic,
            bold=bold,
            width=width,
            height=height,
            x=x,
            y=y,
            batch=self.__batch,
            group=self.__group
        )

    def update(self):
        pass