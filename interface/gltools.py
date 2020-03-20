from pyglet.gl import *
from pyglet.graphics import *

from math import radians, pi, sin, cos

QUARTER_PI = pi/4
HALF_PI = pi/2
PI = pi
TWO_PI = 2*pi
TAU = TWO_PI

def rectangle(x, y, width, height):
    return [
        x, y,
        x + width, y,
        x + width, y + height,
        x, y + height
    ]

def arc(x, y, radius, start, length):
    assert abs(length) <= 2*pi, "Length must be lower or equal than 2*PI"
    count = round(TAU * radius * (length / TAU))
    vertices = []
    for i in range(0, count, 1 if count > 0 else -1):
        angle = length * (i / count) + start
        vertices.append(x + sin(angle) * radius)
        vertices.append(y + cos(angle) * radius)
    return vertices

def createRectangle(x, y, width, height, batch=None, group=None):
    vertices = rectangle(x, y, width, height)
    if batch:
        return batch.add_indexed(len(vertices)//2, GL_TRIANGLES, group,
            [0, 1, 2, 0, 2, 3],
            ('v2f', vertices)
        )
    return vertex_list_indexed(len(vertices)//2,
        [0, 1, 2, 0, 2, 3],
        ('v2f', vertices)
    )

def createRoundRect(x, y, width, height, radius, batch=None, group=None):
    if radius == 0:
        return createRectangle(x, y, width, height, batch, group)
    if type(radius) in (list, tuple):
        assert len(radius) == 4
    else: radius = (radius, radius, radius, radius)
    vertices = []
    vertices.extend(arc(x + radius[0], y + radius[0], radius[0], PI, HALF_PI))
    vertices.extend([x, y+radius[0], x, y+height-radius[1]])

    vertices.extend(arc(x + radius[1], y + height - radius[1], radius[1], -HALF_PI, HALF_PI))
    vertices.extend([x+radius[1], y+height, x+width-radius[2], y+height])

    vertices.extend(arc(x + width - radius[2], y + height - radius[2], radius[2], 0, HALF_PI))
    vertices.extend([x+width, y+height-radius[2], x+width, y+radius[3]])

    vertices.extend(arc(x+width-radius[3], y+radius[3], radius[3], HALF_PI, HALF_PI))
    vertices.extend([x+width-radius[3], y, x+radius[0], y])
    if batch:
        return batch.add(len(vertices)//2, GL_POLYGON, group, ('v2f', vertices))
    return vertex_list(len(vertices)//2, ('v2f', vertices))