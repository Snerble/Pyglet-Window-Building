from componentsv2 import Component
from typing import List, Iterable
from pyglet import gl

class ScrollLayout(Component):
	def __init__(self, parent):
		super().__init__(parent)

		self.size.width.set_value(lambda : self.parent.size.width.value)
		self.size.height.set_value(lambda : self.parent.size.height.value)

		self.size.width.observe(self.parent.size.width)
		self.size.height.observe(self.parent.size.height)

		self._children: List[Component] = list()

		# keeps track of the vertical stack height of this scroll layout
		# important when resizing
		self._oldOffsets: List[float] = list()

		self.__scroll = 0
		self.window.set_handler("on_mouse_scroll", self.on_mouse_scroll)

	@property
	def scroll(self) -> float:
		return self.__scroll
	@scroll.setter
	def scroll(self, value: float):
		cap = sum(self.offsetStack) - self.size.height.value
		self.__scroll = max(0, min(cap, value))
	
	@property
	def offsetStack(self) -> List[float]:
		return [child.size.height.value for child in self._children]

	def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
		self.scroll -= scroll_y * 20

	def add(self, component: Component):
		if (not isinstance(component, Component)):
			raise TypeError(f"Expected {Component.__name__}, got {type(component).__name__} instead.")
		
		self._children.append(component)

	def remove(self, component: Component):
		self._children.remove(component)
		component.parent = None
	
	def clear(self):
		for child in self._children:
			child.parent = None
		self._children.clear()

	def draw(self):
		try:
			self._group.set_state()
			
			def getCoverage(distance: float, *args: Iterable[float]):
				"""Calculates how much of a given array of distances has been
				traversed.

				Args:
					distance (float): The travelled distance.

				Yields:
					float: A value between 0 and 1 denoting how much of the
					       element has been traversed.
				"""
				for height in args:
					yield max(0, min(1, distance / height))
					distance -= height

			offsets = [child.size.height.value for child in self._children]

			# If the amount of components hasn't changed
			if (len(offsets) == len(self._oldOffsets) and offsets != self._oldOffsets):
				# Calculate how much of each child component was scrolled past
				coverages = list(getCoverage(self.scroll, *self._oldOffsets))

				# Calculate a new scroll position
				self.scroll = sum(h * s for h, s in zip(offsets, coverages))

			self._oldOffsets = offsets

			gl.glPushMatrix()
			gl.glTranslatef(0, self.scroll, 0)
			for child in self._children:
				child.draw()
				gl.glTranslatef(0, -child.size.height.value, 0)
			
			gl.glPopMatrix()

			super().draw()
		finally:
			self._group.unset_state()