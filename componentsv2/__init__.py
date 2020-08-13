from .structs import CacheableSize
from .constraints import Value, OffsettableCacheable
from typing import Dict, Any

import pyglet
from pyglet import gl
from pyglet.graphics import Group

class Component:
	def __init__(self, parent, **kwargs: Dict[str, Any]):
		self.name = kwargs.get("name")

		self.__size = CacheableSize[float, float, float, float](0, 0, 0, 0)

		self.__parent = parent
		self._group = ComponentGroup(self, self.parent._group if self.parent else None)
	
	def draw(self):
		return
		gl.glEnable(gl.GL_BLEND)
		gl.glEnable(gl.GL_COLOR_LOGIC_OP)

		gl.glLogicOp(gl.GL_XOR)

		line_width = 3
		x1 = line_width // 2
		y1 = line_width // 2
		x2 = self.size.width.value - x1
		y2 = self.size.height.value - y1

		# Border
		gl.glLineWidth(line_width)
		gl.glColor3f(*((1, ) * 3))
		gl.glBegin(gl.GL_LINES)

		gl.glVertex2f(x1, y1); gl.glVertex2f(x2, y1)
		gl.glVertex2f(x1, y1); gl.glVertex2f(x1, y2)

		gl.glVertex2f(x2, y2); gl.glVertex2f(x1, y2)
		gl.glVertex2f(x2, y2); gl.glVertex2f(x2, y1)

		gl.glEnd()
		
		# Cross
		gl.glLineWidth(0.5)
		gl.glBegin(gl.GL_LINES)

		gl.glVertex2f(x1, y1); gl.glVertex2f(x2, y2)
		# gl.glVertex2f(x1, y2); gl.glVertex2f(x2, y1)

		gl.glEnd()

		gl.glDisable(gl.GL_COLOR_LOGIC_OP)

	@property
	def size(self):
		return self.__size

	@property
	def parent(self) -> 'Component':
		return self.__parent if isinstance(self.__parent, Component) else None
	
	def setParent(self, value: 'Component'):
		"""Setter for the parent property. This is done since properties
		with setters lose their type hints.

		Args:
			value (Component): The new parent component.

		Raises:
			TypeError: `value` is not an instance of Component.
		"""
		if (not isinstance(value, Component)):
			raise TypeError(f"Expected {Component.__name__}, got {type(value).__name__} instead.")
		self.__parent = value

	# @parent.setter
	# def parent(self, value: 'Component'):
	# 	if (not isinstance(value, Component) or value is not None):
	# 		raise TypeError(f"Expected {Component.__name__}, got {type(value).__name__} instead.")
	# 	self.__parent = value

	@property
	def window(self) -> pyglet.window.BaseWindow:
		return (self.__parent.window
			if isinstance(self.__parent, Component)
			else self.__parent
				if isinstance(self.__parent, pyglet.window.BaseWindow)
				else None)
	
	def __repr__(self):
		if self.name is None:
			return super().__repr__()
		return f"{self.__class__.__name__}({self.name})"

class ComponentGroup(Group):
	def __init__(self, component: Component, parent=None):
		super().__init__(parent=parent)
		self._component = component

	def set_state(self):
		gl.glPushMatrix()
		gl.glTranslatef(self._component.size.x.value, self._component.size.y.value, 0)
	
	def unset_state(self):
		gl.glPopMatrix()