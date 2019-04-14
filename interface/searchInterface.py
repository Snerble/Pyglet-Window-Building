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
                        x=window.width//2, y=window.height*0.5,
                        anchor_x='center', anchor_y='center')
    @window.event
    def on_draw():
        draw()
    @window.event
    def on_resize(*args):
        resize(*args)

def loadResources():
    global hexImg
    hexImg = image.load(config.RESOURCES + "stripe.png")

def resize(width, height):
    global imageWall
    global imageWallSprites
    imageWall = graphics.Batch()
    imageWallSprites = []
    for y in range(ceil(height / hexImg.height)):
        for x in range(ceil(width / hexImg.width)):
            imageWallSprites.append(sprite.Sprite(hexImg, hexImg.width*x, hexImg.height*y, batch=imageWall))

def draw(*args):
    window.clear()
    imageWall.draw()
    label.draw()
    