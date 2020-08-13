from enum import Enum

class HorizontalAlign(Enum):
	LEFT = -1
	CENTER = 0
	RIGHT = 1

class VerticalAlign(Enum):
	TOP = -1
	CENTER = 0
	BOTTOM = 1

class Alignment(Enum):
	TOP_LEFT = (HorizontalAlign.LEFT, VerticalAlign.TOP)
	TOP = (HorizontalAlign.CENTER, VerticalAlign.TOP)
	TOP_RIGHT = (HorizontalAlign.RIGHT, VerticalAlign.TOP)

	LEFT = (HorizontalAlign.LEFT, VerticalAlign.CENTER)
	CENTER = (HorizontalAlign.CENTER, VerticalAlign.CENTER)
	RIGHT = (HorizontalAlign.RIGHT, VerticalAlign.CENTER)

	BOTTOM_LEFT = (HorizontalAlign.LEFT, VerticalAlign.BOTTOM)
	BOTTOM = (HorizontalAlign.CENTER, VerticalAlign.BOTTOM)
	BOTTOM_RIGHT = (HorizontalAlign.RIGHT, VerticalAlign.BOTTOM)

	def __init__(self, horizontal: HorizontalAlign, vertical: VerticalAlign):
		self.horizontal = horizontal
		self.vertical = vertical