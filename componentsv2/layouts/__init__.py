from componentsv2 import Component
from typing import List, Iterable

from pyglet import gl
import numpy as np

def getCurrentMatrix() -> np.ndarray:
	a = (gl.GLfloat * 16)()
	gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX, a)
	return np.array(a).reshape(4, 4)

def transpose(matrix, width=4):
	out = list()
	for i in range(0, len(matrix) // width):
		for j in range(0, len(matrix), len(matrix) // width):
			out.append(matrix[i+j])
	return out

class Layout(Component):
	def __init__(self, parent):
		super().__init__(parent)

		# This is used as a set, but it remains a list to maintain the drawing order
		self.__children: List[Component] = list()

	def add(self, component: Component, *args, **kwargs):
		"""Adds the given component to this layout.

		Raises:
			TypeError: `component` is not an instance of Component.
		"""
		if (not isinstance(component, Component)):
			raise TypeError(f"Expected {Component.__name__}, got {type(component).__name__} instead.")

		if (component not in self.__children):
			component.setParent(self)
			self.__children.append(component)
	
	def remove(self, component: Component):
		"""Removes the given component from this layout.
		"""
		self.__children.remove(component)
		component.setParent(None)

	def index(self, component: Component):
		"""Returns the index of the given component in this layout.
		
		Args:
			component (Component): The component whose index to find.

		Raises:
			ValueError: Raised when the given component is not part of this layout.
		"""
		return self.__children.index(component)

	def clear(self):
		"""Clears all children from this layout.
		"""
		for child in self.__children:
			self.remove(child)
	
	def __getitem__(self, key: int):
		return self.__children[key]

	def __len__(self):
		return len(self.__children)
	
	def __iter__(self) -> Iterable[Component]:
		return iter(self.__children)