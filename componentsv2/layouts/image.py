import os

import numpy as np
import pyglet
from pyglet import gl, image
from pyglet.sprite import Sprite

from .. import Component
from ..constraints import Cacheable
from ..structs import CacheableSize
from . import getCurrentMatrix
from .textbox import TextBox


class Image(Component):
	def __init__(self, parent, imagepath):
		super().__init__(parent, name=os.path.splitext(os.path.basename(imagepath))[0])

		self.image: Cacheable[image.AbstractImage] = Cacheable(image.load(imagepath), True)
		self.sprite = Sprite(self.image.value)
		
		self._shape: np.ndarray = None
		self.point: np.ndarray = np.zeros(2)

		self.content_size = CacheableSize[None, None, float, float](None, None, lambda : self.sprite.width, lambda : self.sprite.height)
		self.label = TextBox(self, text=self.name, color=(255, 0, 0, 255), fontsize=12, multiline=True)
		
		# self.size.x.set_value(lambda : (self.parent.size.width.value - self.content_size.width.value))
		self.size.y.set_value(lambda : (self.parent.size.height.value - self.size.height.value))

		self.size.width.set_value(lambda : self.image.value.width)
		self.size.height.set_value(lambda : self.image.value.height)

		# self.size.x.observe(self.parent.size.width)
		self.size.y.observe(self.parent.size.height)
		
		# self.size.x.observe(self.content_size.width)
		self.size.y.observe(self.size.height)

		# self.size.width.observe(self.image)
		# self.size.height.observe(self.image)

		window: pyglet.window.EventDispatcher = self.window
		window.push_handlers()
		window.set_handler("on_mouse_motion", self.on_mouse_motion)

		self.size.width.invalidated += self.on_resize, False
		self.size.height.invalidated += self.on_resize, True

	def on_mouse_motion(self, x, y, dx, dy):
		if self._shape is None:
			return
		
		point = np.array([x, y, 0, 1])
		point = self._shape.T.dot(point)
		point = (self.size.x.value + point[0], self.size.y.value + point[1])
		
		if (self.size.contains(*point)):
			self.point = point
		else:
			self.point = None

	def on_resize(self, isHeight: bool):
		if (isHeight):
			self.size.width.invalidated -= self.on_resize, False
			self.size.width.set_value(self.size.height.value / self.image.value.height * self.image.value.width)
			self.size.width.invalidated += self.on_resize, False
			self.label.font_size = self.size.height.value * 0.1
		else:
			self.size.height.invalidated -= self.on_resize, True
			self.size.height.set_value(self.size.width.value / self.image.value.width * self.image.value.height)
			self.size.height.invalidated += self.on_resize, True
			self.label.size.width.set_value(self.size.width.value)

	def draw(self):
		self.sprite.scale = 1
		self.sprite.scale_x = 1
		self.sprite.scale_y = 1
		self.content_size.invalidate()

		# self.sprite.scale = self.size.height.value / self.image.height
		
		# if (self.sprite.scale != 1):
		# 	self.content_size.invalidate()

		# self.sprite.scale *= max(1, self.size.width.value / self.sprite.width)
		# self.sprite.scale = max((
		# 	self.size.width.value / self.image.width,
		# 	self.parent.size.height.value / self.image.height
		# ))
		# scale = self.size.width.value / self.image.width
		# scale *= min(1, self.parent.size.height.value / (self.image.height * scale))

		# self.sprite.scale = scale

		# self.set_sprite_scale()

		# if (self.sprite.scale != 1):
		# 	self.content_size.invalidate()
		# else:
		# 	if (self.sprite.scale_x != 1):
		# 		self.content_size.width.invalidate()
		# 	if (self.sprite.scale_y != 1):
		# 		self.content_size.height.invalidate()

		self.sprite.scale_x = self.size.width.value / self.image.value.width
		if (self.sprite.scale_x != 1):
			self.content_size.width.invalidate()

		self.sprite.scale_y = self.size.height.value / self.image.value.height
		if (self.sprite.scale_y != 1):
			self.content_size.height.invalidate()
		
		scale_x = self.size.width.value / self.sprite.width
		if (scale_x != 1):
			self.sprite.scale_x *= scale_x
			self.content_size.width.invalidate()
		
		try:
			self._group.set_state()
			self._shape = np.linalg.inv(getCurrentMatrix())
			# gl.glScalef(0.5, 0.5, 1)
			self.sprite.draw()
			self.label.draw()
			super().draw()
		except:
			import traceback
			traceback.print_exc()
			self.sprite.scale = 1
			self.content_size.invalidate()
		finally:
			self._group.unset_state()
		
		if (self.point is not None):
			gl.glBegin(gl.GL_LINES)
			gl.glColor3f(1.0, 0.0, 0.0)
			gl.glVertex2f(self.size.x.value, self.point[1])
			gl.glVertex2f(self.size.x.value + self.size.width.value, self.point[1])

			gl.glVertex2f(self.point[0], self.size.y.value)
			gl.glVertex2f(self.point[0], self.size.y.value + self.size.height.value)
			gl.glEnd()
