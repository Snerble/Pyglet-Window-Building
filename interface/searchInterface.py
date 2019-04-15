from pyglet import gl, graphics, text, clock, image, sprite
# from main import Program
from math import ceil, sin, cos
import config

def init(program):
    global window
    window = program.window
    gl.glClearColor(1.2/100, 6.7/100, 19.2/100, 1)
    
    global label
    label = text.Label('Search',
                        font_name='Verdana',
                        font_size=36,
                        x=window.width//2, y=window.height*0.7,
                        anchor_x='center', anchor_y='center')
    loadResources()
    @window.event
    def on_draw():
        draw()
    @window.event
    def on_resize(*args):
        resize(*args)
    global layout
    document = text.document.FormattedDocument("hello?")
    layout = text.layout.IncrementalTextLayout(document, 120, 50)
    document.align = "center"
    layout.align = "center"
    layout.x = (window.width - 120)/2
    layout.y = window.height * 0.7 - 30 - 50
    document.set_style(0, 9999999, dict(font_name="verdana", font_size=16, color=(255,255,255, 255)))
    caret = text.caret.Caret(layout, color=(255,255,255))
    window.push_handlers(caret)

def loadResources():
    global hexImg
    global imageWall
    global imageWallSprites
    imageWall = graphics.Batch()
    imageWallSprites = dict()

    hexImg = image.load(config.RESOURCES + "stripe.png")

def resize(width, height):
    global hexImg
    global imageWall
    global imageWallSprites
    amountX = ceil(width / hexImg.width)
    amountY = ceil(height / hexImg.height)
    if amountX * amountY != len(imageWallSprites):
        newSprites = dict()
        for y in range(amountY):
            for x in range(amountX):
                if (x, y) in imageWallSprites:
                    # newSprites[(x, y)] = imageWallSprites.pop((x, y))
                    continue
                imageWallSprites[(x, y)] = sprite.Sprite(hexImg, hexImg.width*x, hexImg.height*y, batch=imageWall)
        # for key, icon in imageWallSprites.items():
        #     icon.delete()
        # imageWallSprites = newSprites

def draw(*args):
    window.clear()
    imageWall.draw()
    label.draw()
    layout.draw()
    