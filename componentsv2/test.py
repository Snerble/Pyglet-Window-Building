import random
import os
from typing import get_args

import pyglet
from pyglet import image
from pyglet.sprite import Sprite
from pyglet import gl

import numpy as np

from componentsv2 import Component
from componentsv2.layouts.linearLayout import LinearLayout
from componentsv2.layouts.image import Image
from componentsv2.constraints import Cacheable
from componentsv2.structs import CacheableSize
from tools import listdir, gauge
from etc.events import Event
from componentsv2.scrollLayout import ScrollLayout

_count = 0
def postUpdate():
	"""Increments an update counter that displays an frequency of a certain operation.
	"""
	global _count
	_count += 1

def randomImage():
	path = 'C:\\Users\\Conor\\Google Drive\\Wallpapers'
	# path = 'C:\\Users\\Conor\\Google Drive\\Wallpapers\\Profile Pictures'
	return random.choice(listdir(path, False, lambda x : os.path.isdir(x) or os.path.splitext(x)[1].lower() in (".png", ".jpg"))[0])
	# return random.choice(listdir(path, True)[0])

class TestEnv(Component):
	def __init__(self, parent):
		super().__init__(parent)

		# self.root = ScrollLayout(self)
		self.root = LinearLayout(self)

		self.on_key_press(pyglet.window.key.SPACE, 0)

		self.fps_display = pyglet.window.FPSDisplay(self.window)
		
		self.window.set_handler("on_draw", self.draw)
		self.window.set_handler("on_resize", self.on_resize)
		self.window.set_handler("on_key_press", self.on_key_press)
		# self.window.set_handler("on_mouse_press", self.on_mouse_press)
		pyglet.clock.schedule_interval(self.update, 1/10)

	pressed = None

	def on_mouse_press(self, x, y, button, modifiers):
		TestEnv.pressed = (x, y)

	def update(self, dt, *args):
		global _count
		amount = round(_count / dt)
		print(f"{gauge(amount / 200, 50)} ({amount:3}/s)" + ' ' * 10, end='\r')
		_count = 0

	def on_key_press(self, symbol, modifiers):
		if (symbol == pyglet.window.key.SPACE):
			imagepath = randomImage()

			image = Image(self.root, imagepath)
			
			image.size.width.clear_observations()
			image.size.width.set_value(lambda : image.parent.size.width.value)
			image.size.width.observe(image.parent.size.width)

			image.size.height.clear_observations()
			image.size.height.set_value(lambda : (image.parent.size.width.value / image.image.value.width) * image.image.value.height)
			image.size.height.observe(image.parent.size.width)
			image.size.height.observe(image.image)
			# image.size.height.set_value(lambda : image.parent.size.height.value)
			# image.size.height.observe(image.parent.size.height)

			self.root.add(image)

			print(imagepath)

	def on_resize(self, width, height):
		self.size.width.set_value(width)
		self.size.height.set_value(height)

		# self.root.size.width.set_value(width)
		# self.root.size.height.set_value(height)

	def draw(self):
		self.window.clear()
		try:
			self._group.set_state()

			# pyglet.gl.glMatrixMode(pyglet.gl.GL_PROJECTION)
			# pyglet.gl.glLoadIdentity()
			# pyglet.gl.glOrtho(0.0, self.size.width.value, self.size.height.value, 0.0, -1.0, 1.0)
			# pyglet.gl.glMatrixMode(pyglet.gl.GL_MODELVIEW)
			# pyglet.gl.glLoadIdentity()

			# for child in self.children:
			# 	child.draw()
			
			self.root.draw()

			self.fps_display.draw()
		# except Exception as e:
		# 	print(e)
		finally:
			self._group.unset_state()

def init(program):
	TestEnv(program.window)
