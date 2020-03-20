from pyglet import gl, graphics, media, text, sprite
from math import sin, cos, pi, radians
from tools import runAsNewThread
from interface.gltools import *
from typing import List, Union
import traceback
import os

class Constraint:
    def __init__(self):
        self.__cache = None

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
    def __init__(self, limiter: "lambda"):
        """Initializes a new instance of RelativeConstraint with a function as a value proxy."""
        assert limiter.__class__.__name__ == "function"
        self.__limiter = limiter

    def getValue(self):
        return self.__limiter()
    
    def setValue(self, limiter):
        assert limiter.__class__.__name__ == "function"
        self.__limiter = limiter
    
    @staticmethod
    def toTopOf(component: 'Component'):
        return RelativeConstraint(lambda : component.y)
    @staticmethod
    def toRightOf(component: 'Component'):
        return RelativeConstraint(lambda : component.x + component.width)
    @staticmethod
    def toLeftOf(component: 'Component'):
        return RelativeConstraint(lambda : component.x)
    @staticmethod
    def toBottomOf(component: 'Component'):
        return RelativeConstraint(lambda : component.y + component.height)

class Component:
    def __init__(self, parent=None, **kwargs):
        assert parent == None or issubclass(type(parent), pyglet.window.Window) or issubclass(type(parent), Component)

        # Initialize members
        def set_state():
            gl.glPushMatrix()
            # TODO replace opengl translation with something else
            gl.glTranslatef(self.padding_left, -self.padding_top, 0)
            gl.glTranslatef(self.x, self.y, 0)
        
        def unset_state():
            gl.glPopMatrix()

        self._parent: Component = parent
        self._group = graphics.Group(getattr(self._parent, '_group', None))
        self._group.set_state = set_state
        self._group.unset_state = unset_state

        # Initialize properties
        # self.visible = kwargs.get("visible", True)
        self.x = kwargs.get("x", 0)
        self.y = kwargs.get("y", 0)
        self.width = kwargs.get("width", 0)
        self.height = kwargs.get("height", 0)
        self.max_width = kwargs.get("max_width", None)
        self.max_height = kwargs.get("max_height", None)
        self.padding = kwargs.get("padding", 0)

    def draw(self):
        """Draws the current component."""
        raise NotImplementedError()

    def update(self, *args, **kwargs):
        """TODO Check if nescessary"""
        raise NotImplementedError()

    def set_handlers(self, window):
        """Sets the window handlers used by this component for the specified Pyglet Window."""
        raise NotImplementedError()

    def setPosition(self, x, y):
        """Moves this component to the specified coordinates.
        
        X and Y may also be Constraint instances."""
        self.x = x
        self.y = y
    
    def move(self, x, y):
        """Moves this component the specified amount of pixels from it's current location.

        X and Y must be int or float. If the existing coordinates are Constraint instances,
        they will be overwritten with absolute values."""
        self.x += x
        self.y += y

    @property
    def visible(self) -> bool:
        return self.__visible
    
    @property
    def dimensions(self) -> List[Union[float]]:
        return [float(_) for _ in self.__dimensions]
    @dimensions.setter
    def dimensions(self, value: Union[int, float, Constraint]):
        assert type(value) in (int, float) or issubclass(type(value), Constraint)

    @property
    def x(self):
        return (int(self.__x) if type(self.__x) == int else float(self.__x))
    @x.setter
    def x(self, value):
        Component.calls += 1
        stack = traceback.extract_stack()
        Component.project_func_calls += len(tuple(frame for frame in stack if os.getcwd() in frame.filename))

        print("max_content_height calls: ", Component.calls)
        print("total stack calls: ", Component.project_func_calls)
        if type(value) == str: value = float(value)
        assert type(value) in (int, float) or issubclass(type(value), Constraint)
        self.__x = value

    @property
    def y(self):
        Component.calls += 1
        stack = traceback.extract_stack()
        Component.project_func_calls += len(tuple(frame for frame in stack if os.getcwd() in frame.filename))

        print("max_content_height calls: ", Component.calls)
        print("total stack calls: ", Component.project_func_calls)
        y = int(self.__y) if type(self.__y) == int else float(self.__y)
        window = self.parent
        return window.height - y - self.height if window else y
    @y.setter
    def y(self, value):
        if type(value) == str: value = float(value)
        assert type(value) in (int, float) or issubclass(type(value), Constraint)
        self.__y = value
    
    @property
    def width(self):
        width = int(self.__width) if type(self.__width) == int else float(self.__width)
        max_width = self.max_width
        return max_width if max_width and max_width < width else width
    @width.setter
    def width(self, value):
        # Handle special string values or cast to float
        if type(value) == str:
            if value == "match_parent":
                value = RelativeConstraint(lambda : self.parent.max_content_width if not self.parent == None else 0)
            else:
                value = float(value)
        
        assert type(value) in (int, float) and value >= 0 or issubclass(type(value), Constraint)
        self.__width = value
        
    @property
    def height(self):
        height = int(self.__height) if type(self.__height) == int else float(self.__height)
        max_height = self.max_height
        return max_height if max_height and max_height < height else height
    @height.setter
    def height(self, value):
        # Handle special string values or cast to float
        if type(value) == str:
            if value == "match_parent":
                value = RelativeConstraint(lambda : self.parent.max_content_height if not self.parent == None else 0)
            else:
                value = float(value)
        
        assert type(value) in (int, float) and value >= 0 or issubclass(type(value), Constraint)
        self.__height = value
    
    @property
    def max_width(self):
        if self.__max_width == None: return None
        return int(self.__max_width) if type(self.__max_width) == int else float(self.__max_width)
    @max_width.setter
    def max_width(self, value):
        # Handle special string values or cast to float
        if type(value) == str:
            if value == "match_parent":
                value = RelativeConstraint(lambda : self.parent.width if self.parent else 0)
            else:
                value = float(value)
        
        assert value == None or type(value) in (int, float) and value >= 0 or issubclass(type(value), Constraint)
        self.__max_width = value
    
    @property
    def max_height(self):
        if self.__max_height == None: return None
        return int(self.__max_height) if type(self.__max_height) == int else float(self.__max_height)
    @max_height.setter
    def max_height(self, value):
        # Handle special string values or cast to float
        if type(value) == str:
            if value == "match_parent":
                value = RelativeConstraint(lambda : self.parent.height if self.parent else 0)
            else:
                value = float(value)
        
        assert value == None or type(value) in (int, float) and value >= 0 or issubclass(type(value), Constraint)
        self.__max_height = value

    @property
    def padding(self) -> List[float]:
        return [float(_) for _ in self.__padding]
    @padding.setter
    def padding(self, value: Union[int, float, Constraint, List[Union[int, float, Constraint]]]):
        # If value is a tuple or list, unpack it's elements
        if type(value) in (list, tuple):
            assert not len(value) == 0 and not len(value) > 4, "Value must contain 1-4 elements."
            for v in value: assert type(v) in (int, float) or issubclass(type(v), Constraint), "Invalid type in value."

            if len(value) == 4:
                self.__padding = list(value)
            elif len(value) == 3:
                # TODO use the other padding setters
                self.__padding[0] = value[0] # top
                self.__padding[1] = value[1] # right
                self.__padding[3] = value[1] # left
                self.__padding[2] = value[2] # bottom
            elif len(value) == 2:
                self.__padding[0] = value[0] # top
                self.__padding[2] = value[0] # bottom
                self.__padding[1] = value[1] # right
                self.__padding[3] = value[1] # left
            else:
                self.__padding = (value[0]) * 4
        # Otherwise set the value for all paddings
        else:
            assert type(value) in (int, float) or issubclass(type(value), Constraint), "Expected int, float or Constraint."
            self.__padding = (value,) * 4

    @property
    def padding_top(self) -> float:
        return float(self.__padding[0])
    @padding_top.setter
    def padding_top(self, value: Union[int, float, Constraint]):
        assert type(value) in (int, float) or issubclass(type(value), Constraint), "Expected int, float or Constraint."
        self.__padding[0] = value

    @property
    def padding_right(self) -> float:
        return float(self.__padding[1])
    @padding_right.setter
    def padding_right(self, value: Union[int, float, Constraint]):
        assert type(value) in (int, float) or issubclass(type(value), Constraint), "Expected int, float or Constraint."
        self.__padding[1] = value

    @property
    def padding_bottom(self) -> float:
        return float(self.__padding[2])
    @padding_bottom.setter
    def padding_bottom(self, value: Union[int, float, Constraint]):
        assert type(value) in (int, float) or issubclass(type(value), Constraint), "Expected int, float or Constraint."
        self.__padding[2] = value

    @property
    def padding_left(self) -> float:
        return float(self.__padding[3])
    @padding_left.setter
    def padding_left(self, value: Union[int, float, Constraint]):
        assert type(value) in (int, float) or issubclass(type(value), Constraint), "Expected int, float or Constraint."
        self.__padding[3] = value

    @property
    def max_content_width(self) -> float:
        Component.calls += 1
        stack = traceback.extract_stack()
        Component.project_func_calls += len(tuple(frame for frame in stack if os.getcwd() in frame.filename))

        print("max_content_height calls: ", Component.calls)
        print("total stack calls: ", Component.project_func_calls)
        return self.width - self.padding_left - self.padding_right
    
    calls = 0
    project_func_calls = 0
    @property
    def max_content_height(self) -> float:
        Component.calls += 1
        stack = traceback.extract_stack()
        Component.project_func_calls += len(tuple(frame for frame in stack if os.getcwd() in frame.filename))

        print("max_content_height calls: ", Component.calls)
        print("total stack calls: ", Component.project_func_calls)
        return self.height - self.padding_top - self.padding_bottom

    @property
    def parent(self):
        return self._parent
    @parent.setter
    def parent(self, value):
        self._parent = value
        self._group.value = value

    def contains(self, x, y):
        """Returns whether the given point is inside the boundaries of this component/"""
        return x >= self.x and x < self.x + self.width and y >= self.y and y < self.y + self.height

class Polygon(Component):
    def __init__(self, vertices: list, colors=None, x=0, y=0, **kwargs):
        assert len(vertices) > 0
        assert colors == None or len(colors) == 1 or len(colors) == len(vertices)
        
        width, height = (0,0)
        for vx, vy in vertices:
            if vx > width: width = vx
            if vy > height: height = vy
        super(Polygon, self).__init__(x=x, y=y, widht=width, height=height, **kwargs)
        self._vertices = vertices
        self._colors = colors
    
    def draw(self):
        multiColor = True
        if self._colors:
            if len(self._colors) == 1:
                multiColor = False
                gl.glColor3f(*(c / 255 for c in self._colors[0]))
        i = 0
        self._group.set_state_recursive()
        gl.glBegin(gl.GL_POLYGON)
        while i < len(self._vertices):
            if self._colors and multiColor:
                gl.glColor3f(*(c / 255 for c in self._colors[i]))
            gl.glVertex2f(*self._vertices[i])
            i+=1
        gl.glEnd()
        self._group.unset_state_recursive()

class TextBox(Component):
    def __init__(self, x, y, width, height, radius=0, **kwargs):
        super(TextBox, self).__init__(x, y, width, height)
        self.__batch = kwargs.get("batch")
        self.__group = kwargs.get("group")
        
        if type(radius) in (int, float):
            radius = (radius, radius, radius, radius)
        self.radius = radius
        
        # Create new groups for the background graphics and the textbox foreground
        self.background = graphics.OrderedGroup(0, self._group)
        self.foreground = graphics.OrderedGroup(1, self._group)

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