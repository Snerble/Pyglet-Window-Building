from components import Component, RelativeConstraint
from components.scrollLayout import ScrollLayout
from components.image import Image
from main import Program
from threading import Thread
from interface import xmlParser

import os
import pyglet
import asyncio

def init(program: Program):
    global rootComponent
    rootComponent = TestEnv(program.window)

class TestEnv(Component):
    def __init__(self, parent, **kwargs):
        """Initializes a new TestEnv instance that attaches itself to a window."""
        super().__init__(parent=parent)

        self.parent.set_caption(type(self).__name__)

        widthProxy = RelativeConstraint(lambda : self.parent.width)
        heightProxy = RelativeConstraint(lambda : self.parent.height)

        self.width = RelativeConstraint(lambda : self.parent.width)
        self.height = RelativeConstraint(lambda : self.parent.height)

        self.rootComponent: ScrollLayout = xmlParser.parse("interface/layouts/testEnv.xml")
        self.rootComponent.parent = self
        self.rootComponent.set_handlers(self)

        # Register events
        self.parent.set_handler("on_draw", self.draw)
        self.parent.set_handler("on_key_press", self.on_key_press)
        self.parent.event(self.on_mouse_press)
        self.parent.event(self.on_resize)
        
        pyglet.gl.glClearColor(1.2/100, 6.7/100, 19.2/100, 1)
    
    def on_resize(self, *args):
        self.draw()

    def on_key_press(self, key, modifiers):
        if key == pyglet.window.key.F11:
            self.parent.set_fullscreen(not self.parent._fullscreen)

    def draw(self, *args):
        self.parent.clear()
        self._group.set_state()
        # Draw component
        self.rootComponent.draw()
        # for c in self._children:
        #     c.draw()
        self._group.unset_state()

    def on_mouse_press(self, x, y, button, modifiers):
        print(f"x:{x}, y:{y}, button:{button}, modifiers:{modifiers}")
