from pyglet import gl

class Constraint:
    def getValue(self):
        raise NotImplementedError()
    def setValue(self, value):
        raise NotImplementedError()

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
        if issubclass(type(self.__x), Constraint):
            return self.__x.getValue()
        return self.__x
    @x.setter
    def x(self, x):
        assert type(x) in (int, float) or issubclass(type(x), Constraint)
        self.__x = x

    @property
    def y(self):
        if issubclass(type(self.__y), Constraint):
            return self.__y.getValue()
        return self.__y
    @y.setter
    def y(self, y):
        assert type(y) in (int, float) or issubclass(type(y), Constraint)
        self.__y = y
    
    @property
    def width(self):
        if issubclass(type(self.__width), Constraint):
            return self.__width.getValue()
        return self.__width
    @width.setter
    def width(self, width):
        assert type(width) in (int, float) and width >= 0 or issubclass(type(width), Constraint)
        self.__width = width
        
    @property
    def height(self):
        if issubclass(type(self.__height), Constraint):
            return self.__height.getValue()
        return self.__height
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