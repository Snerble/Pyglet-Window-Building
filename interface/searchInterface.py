import api as E621
import config
import sys

from threading import Thread
from queue import Queue
from tools import runAsNewThread, format_data

from pyglet import gl, graphics, text, clock, image, sprite, media
from pyglet.window import key
from math import ceil, sin, cos

from interface.component import TextBox, RelativeConstraint as Limit

def init(program):
    global initializedHandlers
    initializedHandlers = False

    global window
    window = program.window
    gl.glClearColor(1.2/100, 6.7/100, 19.2/100, 1)
    
    global foreground
    global foregroundBatch
    global background
    global backgroundBatch

    foreground = graphics.OrderedGroup(-1)
    background = graphics.OrderedGroup(-2)
    foregroundBatch = graphics.Batch()
    backgroundBatch = graphics.Batch()

    loadResources()
    window.push_handlers(on_resize=resize, on_draw=draw, on_key_press=on_key_press)
    window.push_handlers(on_mouse_press=mouse_press)

    global textbox
    textbox = TextBox(
        Limit(lambda: (window.width-500)/2),
        Limit(lambda: min(max(window.height/12*11, window.height - 45), window.height - 30)),
        425, 30, 5,
        padding_left=7.5,
        padding_right=7.5,
        batch=foregroundBatch,
        placeholder="Search",
        text="anthro equine female order:favcount type:png",
        group=foreground
    )

    global pagesetter
    pagesetter = TextBox(
        Limit(lambda: (window.width-500)/2 + 500 - 50),
        Limit(lambda: min(max(window.height/12*11, window.height - 45), window.height - 30)),
        50, 30, 5,
        padding_left=7.5,
        padding_right=7.5,
        batch=foregroundBatch,
        text="1",
        group=foreground
    )

    global imageQueue
    global currentPage
    global postList
    imageQueue = Queue()
    currentPage = 1
    postList = (None, None)
    page_size = 100
    # @runAsNewThread("Textbox Activator")
    def activation_action(text):
        global currentPage, postList
        default_cursor = window.get_system_mouse_cursor(window.CURSOR_DEFAULT)
        wait_cursor = window.get_system_mouse_cursor(window.CURSOR_WAIT)

        window.set_mouse_cursor(wait_cursor)
        try:
            query = textbox.document.text
            n = int(pagesetter.document.text) - 1
            if currentPage != n//page_size+1 or postList[0] != query:
                currentPage = n//page_size+1
                postList = (query, list(E621.search(tags=query, limit=page_size, page=currentPage)))
            _post = postList[1][n % page_size]
        except StopIteration:
            print("Found no results, stopping...")
            window.set_mouse_cursor(default_cursor)
            return
        if _post.file_ext in ("webm", "swf"):
            print(f"Found '{_post.file_ext}', stopping...")
            window.set_mouse_cursor(default_cursor)
            return
        window.set_mouse_cursor(default_cursor)

        def file_handler(arg):
            if arg[0].file_ext == "gif":
                img = image.load_animation(arg[1])
            else:
                img = image.load(arg[1])
            arg[0].file_image = img
            imageQueue.put_nowait((arg[0], img))
            clock.schedule_once(update, 0)
            window.set_mouse_cursor(default_cursor)
        window.set_mouse_cursor(wait_cursor)
        if _post.load_file(file_handler) != None:
            imageQueue.put_nowait((_post, _post.load_file()))
            clock.schedule_once(update, 0)
            window.set_mouse_cursor(default_cursor)

    textbox.actions.append(activation_action)
    pagesetter.actions.append(activation_action)

def on_key_press(button, modifiers):
    if button == key.LEFT:
        pagesetter.document.text = str(max(int(pagesetter.document.text)-1, 1))
        textbox.activate()
    if button == key.RIGHT:
        pagesetter.document.text = str(min(int(pagesetter.document.text)+1, 999))
        textbox.activate()

def mouse_press(x, y, button, modifiers):
    window.pop_handlers()
    window.push_handlers()
    if (textbox.contains(x, y)):
        pagesetter.caret.on_mouse_press(x, y, button, modifiers)
        pagesetter.caret.visible = False
        textbox.set_handlers(window)
        textbox.caret.visible = True
        textbox.caret.on_mouse_press(x, y, button, modifiers)
    elif (pagesetter.contains(x, y)):
        textbox.caret.on_mouse_press(x, y, button, modifiers)
        textbox.caret.visible = False
        pagesetter.set_handlers(window)
        pagesetter.caret.visible = True
        pagesetter.caret.on_mouse_press(x, y, button, modifiers)
    else:
        textbox.caret.visible = False
        pagesetter.caret.visible = False
    window.set_handlers(on_mouse_press=mouse_press)

def loadResources():
    global hexImg
    global imageWall
    global imageWallSprites
    imageWall = graphics.Batch()
    imageWallSprites = dict()

    global post
    global postGroup
    global postobject
    global animation
    animation = None
    post = None
    postobject = None
    postGroup = graphics.Group(foreground)

    def set_state():
        global postx, posty, postscale
        padding = (window.height - textbox.y)*2 - textbox.height

        if animation != None: post.scale = 1
        postscale =  min(post.width, window.width) / post.width
        postscale *= min(post.height * postscale, window.height - padding) / (post.height * postscale)

        postx, posty = (window.width - post.width * postscale)/2, (window.height - post.height * postscale - padding)/2
        if animation != None:
            post.x, post.y = postx, posty
            post.scale = postscale

    postGroup.set_state = set_state

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
                imageWallSprites[(x, y)] = sprite.Sprite(hexImg, hexImg.width*x, hexImg.height*y, batch=imageWall, group=background)

def update(dt):
    global post
    global postobject
    global imageQueue
    global animation

    if not animation == None:
        del animation
        animation = None
        # print(post._vertex_list.domain.allocator.get_fragmented_free_size())
        post.delete()
        del post
        post = None
    if not post == None:
        del post
        post = None
    if not postobject == None:
        del postobject
        postobject = None
    del postobject
    del post
    
    postobject, post = imageQueue.get()

    if type(post) == image.Animation:
        animation = post
        post = sprite.Sprite(post, batch=foregroundBatch, group=postGroup)
    else:
        animation = post
        post = sprite.Sprite(post, batch=foregroundBatch, group=postGroup)

    postobject.print()
    try:
        print(format_data(sys.getsizeof(post.get_data(post.format, post.width*len(post.format))), 2))
    except: pass

    if post == None: return
    # post = sprite.Sprite(img, window.width/2, window.height/2, batch=imageWall, group=postGroup)
    # if postobject.file_ext.lower() != "gif":
    #     del img

def draw(*args):
    print("Drawing screen")
    gl.glPushMatrix()
    window.clear()

    imageWall.draw() # draw hex background
    backgroundBatch.draw()
    foregroundBatch.draw()
    
    if animation == None and post != None:
        postGroup.set_state()
        post.blit(postx, posty, width=post.width * postscale, height=post.height * postscale)
        postGroup.unset_state()

    gl.glPopMatrix()
    