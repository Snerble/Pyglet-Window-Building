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
    TestEnv(program.window)

class TestEnv(Component):
    def __init__(self, parent, **kwargs):
        """Initializes a new TestEnv instance that attaches itself to a window."""

        super().__init__(width=parent.width, height=parent.height, parent=parent)

        self.imgMode = "wrap_content"
        self.window.set_caption(type(self).__name__)

        self.rootComponent: ScrollLayout = xmlParser.parse("interface/layouts/testEnv.xml", self)
        self.rootComponent.set_handlers()
        self.rootComponent.padding = 20
    
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
            "https://static1.e621.net/data/bb/de/bbde3ccafc9505a08d3674081052175e.png",
            "https://static1.e621.net/data/55/8d/558dd9c7c8061892d9664d938b2c9183.png",
            "https://static1.e621.net/data/f9/8a/f98ad0611a1bc240715af7b15be361e8.jpg",
            "https://static1.e621.net/data/a3/93/a393c850a6b6923a0d412872e6de0a3f.png",
            "https://static1.e621.net/data/80/c3/80c3b15254f727e44e665f9eb2f3d94c.png",
            "https://static1.e621.net/data/ce/62/ce62df8d3f31101ad0ab060498df0d0b.jpg",
            "https://static1.e621.net/data/fe/b5/feb5afca373a13e0c0121f4b0685dbe3.gif",
            "https://static1.e621.net/data/8c/a4/8ca4ca200341f392d59f7761219db50d.jpg",
            "https://static1.e621.net/data/e3/56/e3566c9dc69f658a5090ed6cd6e3ba10.jpg",
            "https://static1.e621.net/data/22/69/22693d6bc2ec9e7da8369cfe5b7aa751.gif",
            "https://static1.e621.net/data/86/61/866170f314ddad9b70f64107f62ae455.jpg",
            "https://static1.e621.net/data/27/28/2728ed3322326ece2abb6073015d8c9a.jpg",
            "https://static1.e621.net/data/50/82/5082fc5c744f3b75415907ec98a12b19.gif",
            "https://static1.e621.net/data/1d/11/1d112ef3c29c8826f6e48ef8602d7d79.png",

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
                j += 1
                if j < 0: continue
                if j >= 10: break
                image = Image(
                    parent=self.rootComponent,
                    # width="match_parent",
                    # height="match_parent",
                    width="wrap_content",
                    height="wrap_content",
                    # max_width="wrap_content",
                    # max_height="match_parent",
                    # padding_top=0 if j == 1 else 50,
                    # fit_mode="stretch",
                )
                self.rootComponent.add(image)
                image.set_image(file)
                # if j <= 2:
                #     image.image = file
                # else:
                #     image.set_image(file)

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
        self.window.event(self.on_mouse_press)
        
        pyglet.gl.glClearColor(1.2/100, 6.7/100, 19.2/100, 1)

    def on_key_press(self, key, modifiers):
        if key == pyglet.window.key.F11:
            self.window.set_fullscreen(not self.window._fullscreen)
        elif key == pyglet.window.key.SPACE:
            self.imgMode = "wrap_content" if not self.imgMode == "wrap_content" else "match_parent"
            for c in self.rootComponent._ScrollLayout__root_component._children:
                c.width = self.imgMode
                c.height = self.imgMode
            self.draw()

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self.draw()

    def draw(self, *args):
        self.window.clear()
        self._group.set_state()

        self.rootComponent.draw()
        self._group.unset_state()
        self.fps_display.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        print(f"x:{x}, y:{y}, button:{button}, modifiers:{modifiers}")
