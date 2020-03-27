import config
import os
import tempfile

from interface import testEnv, searchInterface

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
        screen = canvas.get_display().get_default_screen()
        try:
            _kwargs = dict(sample_buffers=kwargs.pop("sample_buffers", 1), samples=kwargs.pop("samples", 4))
            _config = Config(**_kwargs)
            _config = screen.get_best_config(_config)
        except:
            print(f"Configuration {_kwargs} failed;. Falling back to default config...")
        finally:
            _config = screen.get_best_config()
        self.window = window.Window(width, height, resizable=True, visible=kwargs.pop("visible", True), config=_config, **kwargs)
        self.window.set_icon(image.load(config.ICON_16x16), image.load(config.ICON_32x32), image.load(config.ICON_128x128))
        if caption: self.window.set_caption(caption)

if __name__ == "__main__":
    if not os.path.exists(tempfile.gettempdir() + config.TEMP_SUBD_DIR):
        os.mkdir(tempfile.gettempdir() + config.TEMP_SUBD_DIR)
    for f in os.listdir(tempfile.gettempdir() + config.TEMP_SUBD_DIR):
        try:
            f = tempfile.gettempdir() + config.TEMP_SUBD_DIR + '/' + f
            os.remove(f)
            print('Removed', f)
        except: pass
    program = Program("E621 Browser")
    testEnv.init(program)
    # searchInterface.init(program)
    app.run()