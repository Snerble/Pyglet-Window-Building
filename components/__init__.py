import os
from math import cos, pi, radians, sin
from typing import Any, Callable, List, Union, Mapping, Optional

from pyglet import gl, graphics, media, sprite, text

from interface.gltools import *
from tools import runAsNewThread
from etc.cachable import Cacheable

class Constraint:
	def __call__(self):
		return self.get_value()

	def get_value(self):
		raise NotImplementedError()
	def set_value(self, value):
		raise NotImplementedError()

	def __int__(self):
		return int(self.get_value())
	def __float__(self):
		return float(self.get_value())

class AbsoluteConstraint(Constraint):
	def __init__(self, value : (int, float)):
		self.__value = value
	
	def get_value(self):
		return self.__value
	def set_value(self, value : (int, float)):
		self.__value = value
	
class RelativeConstraint(Constraint):
	def __init__(self, getter: Callable):
		"""Initializes a new instance of RelativeConstraint with a function as a value proxy."""
		assert getter.__class__.__name__ == "function"
		self.__getter = getter

	def get_value(self):
		return self.__getter()
	
	def set_value(self, getter):
		assert getter.__class__.__name__ == "function"
		self.__getter = getter
	
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
			gl.glTranslatef(self.padding_left, self.padding_bottom, 0)
			gl.glTranslatef(self.x, self.y, 0)
		
		def unset_state():
			gl.glPopMatrix()

		self.__cache = dict()
		self.__value_watchers: List[Mapping[Component, str, str]] = list() # mapping is [caller, src value name, tgt value name]

		self.__parent: Component = parent
		self.__bounds: List[Union[int, float, Constraint]] = [0, 0, 0, 0]
		self.__padding: List[Union[int, float, Constraint]] = [0, 0, 0, 0]
		self.__max_size: List[Union[None, int, float, Constraint]] = [None, None]
		
		self._group = graphics.Group(getattr(self.parent, '_group', None))
		self._group.set_state = set_state
		self._group.unset_state = unset_state

		# Initialize properties
		self.visible = kwargs.get("visible", True)

		self.x = kwargs.get("x", 0)
		self.y = kwargs.get("y", 0)
		self.width = kwargs.get("width", 0)
		self.height = kwargs.get("height", 0)
		if "bounds" in kwargs: self.bounds = kwargs["bounds"]

		self.max_width = kwargs.get("max_width", None)
		self.max_height = kwargs.get("max_height", None)

		self.padding_top = kwargs.get("padding_top", 0)
		self.padding_right = kwargs.get("padding_right", 0)
		self.padding_bottom = kwargs.get("padding_bottom", 0)
		self.padding_left = kwargs.get("padding_left", 0)
		if "padding" in kwargs: self.padding = kwargs["padding"]

		# Configure internal relations
		Component.width.on_update[self] += Component.max_content_width.fdel, self # Clears the max_content_width cache if width changes
		# Component.height.on_update[self] += Component.max_content_height.fdel, self

		Component.max_width.on_update[self] += Component.width.fdel, self # Clears the width cache if max_width changes
		# Component.max_height.on_update[self] += Component.height.fdel, self

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
	@visible.setter
	def visible(self, value: bool):
		assert type(value) == bool, "Expected bool."
		self.__visible = value
		# TODO invalidate component
	
	@property
	def bounds(self) -> List[Union[float]]:
		return [float(_) for _ in self.__bounds]
	@bounds.setter
	def bounds(self, value: List[Union[int, float, Constraint]]):
		assert type(value) in (list, tuple), "Ordered list type expected."
		assert len(value) == 4, "Expected 4 elements."
		self.x, self.y, self.width, self.height = value

	@property
	def x(self):
		return (int(self.__bounds[0]) if type(self.__bounds[0]) == int else float(self.__bounds[0]))
	@x.setter
	def x(self, value):
		if type(value) == str: value = float(value)
		assert type(value) in (int, float) or issubclass(type(value), Constraint)
		self.__bounds[0] = value

	@property
	def y(self) -> Union[int, float]:
		y = int(self.__bounds[1]) if type(self.__bounds[1]) == int else float(self.__bounds[1])
		window = self.parent
		return window.max_content_height - y - self.height if window else y
	@y.setter
	def y(self, value: Union[str, int, float, Constraint]):
		if type(value) == str: value = float(value)
		assert type(value) in (int, float) or issubclass(type(value), Constraint)
		self.__bounds[1] = value
	
	@Cacheable
	def width(self) -> Union[int, float]:
		width = int(self.__bounds[2]) if type(self.__bounds[2]) == int else float(self.__bounds[2])
		return min(self.max_width, width) if self.max_width else width
	@width.setter
	def width(self, value: Union[str, int, float, Constraint]):
		# Handle special string values or cast to float
		remove_event = True
		if type(value) == str:
			if value == "match_parent":
				value = RelativeConstraint(lambda : self.parent.max_content_width if not self.parent == None else 0)
				# Add callback to the parent max_content_width that clears this width cache
				Component.max_content_width.on_update[self.parent] += Component.width.fdel, self
				remove_event = False
			else:
				# TODO parse special value units
				value = float(value)
		
		assert type(value) in (int, float) and value >= 0 or issubclass(type(value), Constraint)

		# Remove the max_content_width callback from the parent
		if remove_event: Component.max_content_width.on_update[self.parent] -= Component.width.fdel, self

		self.__bounds[2] = value

	@property
	def height(self) -> float:
		if issubclass(type(self.__bounds[3]), Constraint):
			height = self.__get_cache("height", self.__bounds[3])
		else:
			height = self.__bounds[3]

		max_height = self.max_height
		return min(max_height, height) if max_height else height
	@height.setter
	def height(self, value: Union[str, int, float, Constraint]):
		# Handle special string values or cast to float
		remove_watcher = True
		if type(value) == str:
			if value == "match_parent":
				value = RelativeConstraint(lambda : self.parent.max_content_height if not self.parent == None else 0)
				self.set_value_watcher(self.parent, "height", "max_content_height")
				remove_watcher = False
			else:
				value = float(value)
		
		assert type(value) in (int, float) and value >= 0 or issubclass(type(value), Constraint)

		# Clear this value's cache and remove the match_parent value watcher (if present)
		self.__cache.pop("height", None)
		if remove_watcher: self.remove_value_watcher(self.parent, "height", "max_content_height")
		
		self.__bounds[3] = value

		# TODO invalidate instead of notifying the watchers here (max_content_height may or may not be cached)
		# Notify the watchers on related values
		self.notify_value_watchers("max_content_height")
	@height.deleter
	def height(self):
		self.__cache.pop("height", None)
		self.notify_value_watchers("max_content_height")
	
	@Cacheable
	def max_width(self) -> Union[float, None]:
		if self.__max_size[0] == None: return None
		return int(self.__max_size[0]) if type(self.__max_size[0]) == int else float(self.__max_size[0])
	@max_width.setter
	def max_width(self, value: Union[str, int, float, Constraint]):
		# Handle special string values or cast to float
		remove_event = True
		if type(value) == str:
			if value == "match_parent":
				value = RelativeConstraint(lambda : self.parent.max_content_width if self.parent else 0)
				# Add callback to the parent max_content_width that clears this max_width cache
				Component.max_content_width.on_update[self.parent] += Component.max_width.fdel, self
				remove_event = False
			else:
				# TODO parse special value units
				value = float(value)

		assert value == None or type(value) in (int, float) and value >= 0 or issubclass(type(value), Constraint)
		
		# Remove the max_content_width callback from the parent
		if remove_event: Component.max_content_width.on_update[self.parent] -= Component.max_width.fdel, self

		self.__max_size[0] = value
	
	@property
	def max_height(self) -> Union[float, None]:
		# Try to use the cache if the value is a constraint
		if issubclass(type(self.__max_size[1]), Constraint):
			return self.__get_cache("max_height", self.__max_size[1])

		# Return the value by default
		if self.__max_size[1] == None: return None
		return int(self.__max_size[1]) if type(self.__max_size[1]) == int else float(self.__max_size[1])
	@max_height.setter
	def max_height(self, value: Union[str, int, float, Constraint]):
		# Handle special string values or cast to float
		remove_watcher = True
		if type(value) == str:
			if value == "match_parent":
				value = RelativeConstraint(lambda : self.parent.max_content_height if self.parent else 0)
				self.set_value_watcher(self.parent, "max_height", "max_content_height")
				remove_watcher = False
			else:
				value = float(value)

		assert value == None or type(value) in (int, float) and value >= 0 or issubclass(type(value), Constraint)
		
		# Clear this value's cache
		self.__cache.pop("max_height", None)
		if remove_watcher: self.remove_value_watcher(self.parent, "max_height", "max_content_height")

		self.__max_size[1] = value

		# Notify value watchers for related values
		self.notify_value_watchers("height")
		self.notify_value_watchers("max_content_height")
	@max_height.deleter
	def max_height(self):
		self.__cache.pop("max_height", None)
		# Notify watchers for related values
		self.notify_value_watchers("height")
		self.notify_value_watchers("max_content_height")

	@property
	def padding(self) -> List[float]:
		return [float(_) for _ in self.__padding]
	@padding.setter
	def padding(self, value: Union[str, int, float, Constraint, List[Union[int, float, Constraint]]]):
		# Handle special string values
		if type(value) == str: value = tuple(float(t) for t in value.split())
		
		# If value is a tuple or list, unpack it's elements
		if type(value) in (list, tuple):
			assert not len(value) == 0 and not len(value) > 4, "Value must contain 1-4 elements."
			if len(value) == 4:
				self.padding_top    = value[0]
				self.padding_right  = value[1]
				self.padding_bottom = value[2]
				self.padding_left   = value[3]
			elif len(value) == 3:
				# TODO use the other padding setters
				self.padding_top    = value[0]
				self.padding_right  = value[1]
				self.padding_left   = value[1]
				self.padding_bottom = value[2]
			elif len(value) == 2:
				self.padding_top    = value[0]
				self.padding_bottom = value[0]
				self.padding_right  = value[1]
				self.padding_left   = value[1]
			else:
				self.padding = value[0] # recurse with the single element
		# Otherwise set the value for all paddings
		else:
			assert type(value) in (int, float) or issubclass(type(value), Constraint), "Expected int, float or Constraint."
			# The padding is set this way as to not circumvent additional functionality in the seperate setters
			self.padding_top    = value
			self.padding_right  = value
			self.padding_bottom = value
			self.padding_left   = value

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

	@Cacheable
	def max_content_width(self) -> float:
		return self.width - self.padding_left - self.padding_right
	
	@property
	def max_content_height(self) -> float:
		return self.height - self.padding_top - self.padding_bottom

	@property
	def parent(self) -> 'Component':
		return self.__parent if not type(self.__parent) == pyglet.window.Window else None
	@parent.setter
	def parent(self, value: Union[None, 'Component', pyglet.window.Window]):
		# Set this group's parent if the value is a component
		if issubclass(type(value), Component):
			self._group.parent = value._group

			# Transfer this component's value watchers on the old parent to the new parent
			for item in self.__parent.__value_watchers[:]:
				if item[0] == self:
					self.__parent.__value_watchers.remove(item)
					value.__value_watchers.append(item)
		else:
			# Remove the value watchers from the old parent
			for item in self.__parent.__value_watchers[:]:
				if item[0] == self:
					self.__parent.__value_watchers.remove(item)

		self.__parent = value

	@property
	def window(self) -> pyglet.window.Window:
		if self.__parent == None:
			return None
		if type(self.__parent) == pyglet.window.Window:
			return self.__parent
		# Recurse until a pyglet window (or none) is found
		return self.__parent.window

	def contains(self, x: Union[int, float], y) -> bool:
		"""Returns whether the given point is inside the boundaries of this component/"""
		return x >= self.x and x < self.x + self.width and y >= self.y and y < self.y + self.height
	
	def set_value_watcher(self, target: 'Component', watcher: Union[str, Callable], tgt_value_name: str, *args: Any, **kwargs: Any):
		"""Registers a value watcher on on the specified attribute of the target component.
		
		Args:
			target: Component -> The target component to register a value watcher on.
			watcher:
				str             -> The name of the value to delete from 'self' using the delattr() function.
								   This is a shortcut that allows a property deleter to be used for removing
								   cached values.
				Callable        -> A function or lambda that should be called when the target value changes.
			tgt_value_name: str -> The name of the value to watch on the target component.
			args: Any           -> A list of arguments to pass to the watcher if it is a Callable. Otherwise ignored.
			kwargs: Any         -> A list of keyword arguments to pass to the watcher if it is a Callable. Otherwise ignored.
		"""
		assert not tgt_value_name.startswith('_'), "Registering callbacks for private or protected values is forbidden."

		# Create the value watcher list item
		watcher_entry = [self, watcher, tgt_value_name]
		if not type(watcher) == str:
			watcher_entry.append(args)
			watcher_entry.append(kwargs)
		# if not len(args) == 0: watcher_entry.append(args)
		# if not len(kwargs) == 0: watcher_entry.append(kwargs)
		watcher_entry = tuple(watcher_entry)

		# Remove the old value watcher if it is present
		for item in target.__value_watchers:
			if watcher_entry[:3] == item[:3]:
				target.__value_watchers.remove(item)
				break
		
		# Add the value watcher to the target component
		target.__value_watchers.append(watcher_entry)
	
	def remove_value_watcher(self, target: 'Component', watcher: Union[str, Callable], tgt_value_name: str):
		"""Removes the specified value watcher from the target component.
		
		Args:
			target: Component   -> The component to remove the value watcher from.
			watcher:
				str             -> The name of the value that is watching the target value.
				Callable        -> The callable that is watching the target value.
			tgt_value_name: str -> The name of the value that is being watched.
		"""
		if target == None: return
		for item in target.__value_watchers:
			if (self, watcher, tgt_value_name) == item[:3]:
				target.__value_watchers.remove(item)
				return
	
	def notify_value_watchers(self, value_name: str):
		"""Triggers all value watchers registered on the specified value."""
		for item in self.__value_watchers:
			if value_name == item[2]:
				if type(item[1]) == str:
					# Use the delattr function if the value watcher is not a callback
					delattr(item[0], item[1])
				else:
					# Otherwise, invoke the watcher callback
					item[1](*item[3], **item[4])

	def __del_cache(self, key: str):
		self.__cache.pop(key, None)

	def __get_cache(self, key: str, getter: Constraint) -> Any:
		value = self.__cache.get(key, None)
		if value == None:
			value = getter.get_value()
			self.__cache[key] = value
		return value

	def __setattr__(self, name: str, value: Any):
		super().__setattr__(name, value)

		# Notify value watchers (only for public values)
		if not name.startswith('_'):
			self.notify_value_watchers(name)
	
	def __delattr__(self, name: str):
		super().__delattr__(name)

		# Notify value watchers (only for public values)
		if not name.startswith('_'):
			self.notify_value_watchers(name)

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
