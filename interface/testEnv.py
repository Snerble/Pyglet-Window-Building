from components import Component, RelativeConstraint
from components.scrollLayout import ScrollLayout
from components.image import Image
from main import Program
from threading import Thread
from interface import xmlParser

import tools
import os
import pyglet
import asyncio
import api

def init(program: Program):
    pyglet.gl.glGenFramebuffers(1, pyglet.gl.GLuint())

    TestEnv(program.window)

class TestEnv(Component):
    def __init__(self, parent, **kwargs):
        """Initializes a new TestEnv instance that attaches itself to a window."""

        super().__init__(width=parent.width, height=parent.height, parent=parent)

        self.imgMode = "wrap_content"
        self.window.set_caption(type(self).__name__)

        self.rootComponent: ScrollLayout = xmlParser.parse("interface/layouts/testEnv.xml", self)
        self.rootComponent.set_handlers()
        # self.rootComponent.padding = 20
    
        def getfiles(path):
            items = list(os.path.join(path, _) for _ in os.listdir(path))

            dirs = list(_ for _ in items if os.path.isdir(_))
            files = list(_ for _ in items if os.path.isfile(_) and not os.path.splitext(_)[1] == ".zip")

            for d in dirs:
                _files, _dirs = getfiles(d)
                files.extend(_files)
                dirs.extend(_dirs)

            return files, dirs

        path = r"C:\Users\conor\Google Drive\Wallpapers\Profile Pictures"
        files, _ = getfiles(path)
        self.fps_display = pyglet.window.FPSDisplay(self.window)

        urls = [
        ]


        if False:
            for url in urls:
                image = Image(
                    parent=self.rootComponent,
                    width="match_parent",
                    height="match_parent",
                    max_height="wrap_content",
                    max_width="wrap_content",
                    fit_mode="stretch"
                )
                self.rootComponent.add(image)
                image.set_image(url)
        else:
            j = 0
            for file in files:
                if j < 0: continue
                if j >= 100: break
                image = Image(
                    parent=self.rootComponent,
                    # width="match_parent",
                    # height="match_parent",
                    width="match_parent",
                    height="match_parent",
                    # max_width="wrap_content",
                    # max_height="match_parent",
                    # padding_top=0 if j == 1 else 50,
                    fit_mode="fill",
                )
                self.rootComponent.add(image)
                image.set_image(file)
                # if j <= 2:
                #     image.image = file
                # else:
                #     image.set_image(file)
                j += 1

        # img = pyglet.image.load(files[0])
        # for i in range(15):
        #     image = Image(
        #         parent=self.rootComponent,
        #         width="match_parent",
        #         height="wrap_content",
        #         # max_width="match_parent",
        #         # max_height="match_parent",
        #     )
        #     self.rootComponent.add(image)
        #     image.set_image(img)

        # Register events
        self.window.set_handler("on_draw", self.draw)
        self.window.set_handler("on_resize", self.on_resize)
        self.window.set_handler("on_key_press", self.on_key_press)
        self.window.set_handler("on_close", self.on_close)
        self.window.set_handler("on_deactivate", self.on_deactivate)
        
        pyglet.gl.glClearColor(1.2/100, 6.7/100, 19.2/100, 1)

    def on_deactivate(*args):
        print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")

    def on_key_press(self, key, modifiers):
        if key == pyglet.window.key.F11:
            fullscreen = not self.window.fullscreen

            target_screen = None
            if fullscreen:
                # Get the middle of the window to determine the most suitable screen
                window_pos = self.window.get_location()
                window_pos = (
                    window_pos[0] + self.window.width / 2,
                    window_pos[1] + self.window.height / 2
                )

                # Find the first screen that contains the window position
                for screen in pyglet.canvas.get_display().get_screens():
                    if (window_pos[0] >= screen.x and window_pos[0] < screen.x + screen.width and
                        window_pos[1] >= screen.y and window_pos[1] < screen.x + screen.width):
                        target_screen = screen
                        break

            self.window.set_fullscreen(fullscreen, screen=target_screen)
        elif key == pyglet.window.key.SPACE:
            self.imgMode = "wrap_content" if not self.imgMode == "wrap_content" else "match_parent"
            for c in self.rootComponent._ScrollLayout__root_component._children:
                c.width = self.imgMode
                # c.height = self.imgMode
            self.draw()
    
    @pyglet.app.event_loop.event
    def on_window_close(self):
        print("on_window_close")
    
    @staticmethod
    @pyglet.app.event_loop.event
    def on_exit():
        print("on_exit")
    
    def on_close(self):
        print("on_close")

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self.draw()

    def draw(self, *args):
        pyglet.gl.glClearColor(1.2/100, 6.7/100, 19.2/100, 1)
        self.window.clear()
        self._group.set_state()

        self.rootComponent.draw()
        self._group.unset_state()
        self.fps_display.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        print(f"x:{x}, y:{y}, button:{button}, modifiers:{modifiers}")
