import config
# from interface.component import *
from interface import searchInterface

from pyglet import *
from pyglet.gl import *
import pyglet_ffmpeg as ffmpeg
ffmpeg.load_ffmpeg()

class Program:
    def __init__(self, caption=None, width=1280, height=720, **kwargs):
        """
        Initializes a new Program with the given parameters.

        There are also various kwargs to specify. Here they are denoted in the following format:
            [default] name: description.
        The kwargs are:
            [1] sample_buffers: Used in the window config. See pyglet's documentation on gl.Config for more.
            [4] samples:        The levels of anti_alias. See pyglet's documentation on gl.Config for more.
            [True] visible:     Set whether the window starts as visible.
        The remaining kwargs will be passed to the pyglet.window.Window() constructor. See the
        pyglet.window.Window() documentation for more info.
        """
        _config = Config(sample_buffers=kwargs.pop("sample_buffers", 1), samples=kwargs.pop("samples", 4))
        self.window = window.Window(width, height, resizable=True, visible=kwargs.pop("visible", True), config=_config, **kwargs)
        self.window.set_icon(image.load(config.ICON_16x16), image.load(config.ICON_32x32))
        if caption: self.window.set_caption(caption)

        @self.window.event
        def on_draw(*args):
            self.on_draw(*args)
        @self.window.event
        def on_resize(*args):
            self.on_resize(*args)
        @self.window.event
        def on_key_press(*args):
            self.on_key_press(*args)

    def on_draw(self):
        pass

    def on_resize(self, width, height):
        pass

    def on_key_press(self, symbol, modifiers):
        pass
    
    def update(self, dt):
        pass

if __name__ == "__main__":
    program = Program("E621 Browser")
    searchInterface.init(program)
    app.run()