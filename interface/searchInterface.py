import config

from pyglet import gl, graphics, text, clock, image, sprite
from math import ceil, sin, cos

from interface.component import TextBox, RelativeConstraint as Limit

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

    global textbox
    textbox = TextBox(
        Limit(lambda: window.width/2-100),
        Limit(lambda: window.height/2-50),
        200, 50, (10, 15, 10, 10),
        batch=imageWall,
        text="Hello?",
        color=(255,0,0,255),
        italic=True,
        bold=True
    )
    textbox.push_handlers(window)

    clock.schedule_interval(update, 1/60)

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
        for y in range(amountY):
            for x in range(amountX):
                if (x, y) in imageWallSprites: continue
                imageWallSprites[(x, y)] = sprite.Sprite(hexImg, hexImg.width*x, hexImg.height*y, batch=imageWall)

def update(dt):
    pass

def draw(*args):
    gl.glPushMatrix()
    window.clear()

    imageWall.draw() # draw hex background
    label.draw() # draw 'search' text label

    gl.glPopMatrix()
    