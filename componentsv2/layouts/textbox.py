from . import Component

from pyglet import gl
from pyglet.text import Label, layout
from typing import TypeVar, Tuple

Color = TypeVar("Color", bound=Tuple[int, int, int, int])

class TextBox(Component):
	def __init__(self, parent, **kwargs: dict):
		super().__init__(parent, **kwargs)

		self.__label = Label(width=1, align='center', bold=True, anchor_y='bottom')

		for key, value in kwargs.items():
			if (not key.startswith('_')):
				setattr(self, key, value)
		
		self.size.width.invalidated += lambda : self.__label._set_width(self.size.width.value or 1)
		# self.size.height.invalidated += lambda : self.__label._set_height(self.size.height.value or 1)

	@property
	def text(self):
		return self.__label.text
	@text.setter
	def text(self, value: str):
		self.__label.text = value

	@property
	def multiline(self):
		return self.__label.multiline
	@multiline.setter
	def multiline(self, value: bool):
		self.__label.multiline = value
	
	@property
	def font_size(self):
		return self.__label.font_size
	@font_size.setter
	def font_size(self, value: float):
		self.__label.font_size = value

	@property
	def color(self) -> Color:
		return self.__label.color
	@color.setter
	def color(self, value: Color):
		self.__label.color = value

	def draw(self):
		try:
			self._group.set_state()

			self.size.height.set_value(self.__label.content_height)

			self.__label.draw()
			super().draw()
		finally:
			self._group.unset_state()
		