from pyglet import gl, graphics, media, text
from math import sin, cos, pi, radians

class Constraint:
    def getValue(self):
        raise NotImplementedError()
    def setValue(self, value):
        raise NotImplementedError()
    
    def __int__(self):
        return self.getValue()
    def __float__(self):
        return self.getValue()

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
    def __init__(self, x=0, y=0, width=0, height=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def draw(self):
        raise NotImplementedError()
    
    def __call__(self, *args, **kwargs):
        self.draw()
        return 0

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

class Rectangle(Component):
    def __init__(self, x=0, y=0, width=0, height=0, color=(255, 255, 255)):
        super(Rectangle, self).__init__(x, y, width, height)
        self._color = (c / 255 for c in color)

    def draw(self, batch):
        gl.glColor3f(*self._color)
        gl.glBegin(gl.GL_QUADS)
        gl.glTranslatef(self.x, self.y, 0)
        gl.glVertex2f(0)
        gl.glVertex2f(self.width, 0)
        gl.glVertex2f(self.width, self.height)
        gl.glVertex2f(0, self.height)
        gl.glTranslatef(-self.x, -self.y, 0)
        gl.glEnd()

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

class RoundRect(Component):
    def __init__(self, x, y, width, height, radius, r2=None, r3=None, r4=None, color=None):
        assert radius != None and (len({r2,r3,r4}) == 1 or len({radius,r2,r3,r4}) == 1)
        super(RoundRect, self).__init__(x, y, width, height)
        if r2 == None:
            self.radii = (radius, radius, radius, radius)
        else:
            self.radii = (radius, r2, r3, r4)
        self._vertices = self._getVertices()
    
    def _getVertices(self):
        out = []
        def arc(x, y, radius, start, length):
            out = []
            steps = int(2 * pi * radius)
            for i in range(steps):
                angle = radians(360 * (i / steps)) + start
                if angle > length + start: break
                out.append(self.x + x + sin(angle) * radius)
                out.append(self.y + y + cos(angle) * radius)
            if len(out) == 0:
                out.extend([self.x+x, self.y+y])
            return out
        out.extend(arc(self.radii[3], self.radii[3]*-1 + self.height, self.radii[3], -pi/2, pi/2)) # upper left
        out.extend(arc(self.radii[2]*-1 + self.width, self.radii[2]*-1 + self.height, self.radii[2], 0, pi/2)) # upper right 
        out.extend(arc(self.radii[1]*-1 + self.width, self.radii[1], self.radii[1], pi/2, pi/2)) # lower right
        out.extend(arc(self.radii[0], self.radii[0], self.radii[0], pi, pi/2)) # lower left
        return out

    def draw(self, batch: graphics.Batch = None):
        graphics.draw(len(self._vertices)//2, gl.GL_POLYGON,
            ('v2f', self._vertices)
        )
        if batch:
            batch.add(len(self._vertices)//2, gl.GL_POLYGON, None,
                ('v2f', self._vertices)
            )
        # graphics.draw(2, gl.GL_LINES,
        #     ('v2f', (self.x+5+self.width, self.y, self.x+5+self.width, self.y+self.height)),
        #     ('c3B', (255,255,0, 255,0,0))
        # )
        # graphics.draw(2, gl.GL_LINES,
        #     ('v2f', (self.x, self.y-5, self.x+self.width, self.y-5)),
        #     ('c3B', (255,255,0, 255,0,0))
        # )

class TextBox(RoundRect):
    def __init__(self, x, y, width, height, radius=0, **kwargs):
        super(TextBox, self).__init__(x, y, width, height, radius)
        _text = kwargs.get("text", "")

        self.document = text.document.FormattedDocument(kwargs.get("text", ''))
        self.document.set_style(0, len(self.document.text), dict(
            font_name=kwargs.get("font_name", "Sans-Serif"),
            font_size=kwargs.get("font_size", 16),
            bold=kwargs.get("bold", False),
            italic=kwargs.get("italic", False),
            color=kwargs.get("color", (0,0,0,255))
        ))
        self.layout = text.layout.IncrementalTextLayout(self.document, width, height)
        self.layout.content_valign = "center"
        
        self.caret = text.caret.Caret(self.layout, color=kwargs.get("caret_color", (0,0,0)))
    
        self.layout.x = self.x
        self.layout.y = self.y
    
    def update(self):
        self.layout.x = self.x
        self.layout.y = self.y
        self._vertices = self._getVertices()
    
    def draw(self, *args):
        super(TextBox, self).draw(*args)
        # self.layout.draw()

    def push_handlers(self, window):
        window.push_handlers(self.caret)