#!/usr/bin/env python3

import config
import tools
import api
import os
import threading
import tempfile
import sys
import time
import queue

import pyglet
import pyglet_ffmpeg as ffmpeg
ffmpeg.load_ffmpeg()

if not os.path.exists(tempfile.gettempdir() + config.TEMP_SUBD_DIR):
    os.mkdir(tempfile.gettempdir() + config.TEMP_SUBD_DIR)
for f in os.listdir(tempfile.gettempdir() + config.TEMP_SUBD_DIR):
    try:
        f = tempfile.gettempdir() + config.TEMP_SUBD_DIR + '\\' + f
        os.remove(f)
        print('Removed', f)
    except: pass

query = input('Enter a search query: ')

window = pyglet.window.Window(visible=False, resizable=True)
fps_display = pyglet.window.FPSDisplay(window)
batch = pyglet.graphics.Batch()
batch_sprites = []
batch_sprites.clear
batch_lock = threading.Condition(threading.Lock())

page = 0
column_width = list()
row_height = list()
row_width = list()
posts = list()
post_image_queue = queue.Queue()
sprite_deletion = queue.Queue()

def catch(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(e)
    return wrapper

def event_controlled(activator, terminator=None):
    def func_getter(func):
        def wrapper(*args, **kwargs):
            _args = args
            _kwargs = kwargs
            while True:
                if not terminator == None and terminator.is_set():
                    return
                args = _args
                kwargs = _kwargs
                activator.wait(1)
                if not activator.is_set():
                    continue
                try:
                    activator.args
                    if not len(activator.args) == 0:
                        args = activator.args
                except: pass
                try:
                    activator.kwargs
                    if not len(activator.kwargs) == 0:
                        kwargs = activator.kwargs
                except: pass
                func(*args, **kwargs)
                activator.clear()
            return
        return wrapper
    return func_getter

threads = []
def new_thread(func, *args, **kwargs):
    process = threading.Thread(target=func, args=args, kwargs=kwargs)
    process.start()
    threads.append(process)

navigate_page = threading.Event()
def _set(*args, **kwargs):
    navigate_page.args = args
    navigate_page.kwargs = kwargs
    with navigate_page._cond:
        navigate_page._flag = True
        navigate_page._cond.notify_all()
navigate_page.set = _set

program_stop = threading.Event()
@event_controlled(navigate_page, program_stop)
def loadPage(incr=1, **kwargs):
    global page, posts, column_width, row_height, batch_sprites, row_width
    npage = tools.constrain(page+incr, 1, 750)
    if npage == page:
        return
    page = npage

    nposts = list(api.search(1, tags=query, page=page))

    for post in posts:
        post.clear_cache()
    posts.clear()
    posts.extend(nposts)
    with batch_lock:
        while len(batch_sprites) < len(posts):
            batch_sprites.append(None)
        index = len(batch_sprites)-1
        for i in range(len(batch_sprites) - len(posts)):
            sprite_deletion.put_nowait(batch_sprites[index])
            index -= 1

    _column_width = []
    _row_height = []
    row_width = []

    index = 0
    for post in posts:
        column = index % 11
        row = index // 11

        post.column = column
        post.row = row
        #width = post.width
        #height = post.height
        width = post.preview_width
        height = post.preview_height

        if len(_column_width) > column:
            if width > _column_width[column]:
                _column_width[column] = width
        else:
            _column_width.append(width)

        if len(_row_height) > row:
            if height > _row_height[row]:
                _row_height[row] = height
        else:
            _row_height.append(height)
        index += 1

    index = 0
    for post in posts:
        column = index % 11
        row = index // 11

        if len(row_width) > row:
            row_width[row] += _column_width[column] + 20
        else:
            row_width.append(_column_width[column]+20)
        
        index += 1

    column_width = list(map(lambda x:x+20, _column_width[:-1]))
    column_width.extend(_column_width[-1:])
    row_height = list(map(lambda x:x+20, _row_height[:-1]))
    row_height.extend(_row_height[-1:])
    row_width = list(map(lambda x:x-20, row_width))[::-1]

    index = 0
    image_lock = threading.Condition(threading.Lock())
    vid_handler = lambda x: post_image_queue.put_nowait(x)
    def file_handler(x):
        post, file = x
        try:
            with image_lock:
                ext = os.path.splitext(file)[1]
                if 'animated' in post.tags.split(' ') and ext == '.gif':
                    image = pyglet.image.load_animation(file)
                else:
                    image = pyglet.image.load(file)
                post_image_queue.put_nowait((post, image))
        except Exception as e:
            print(e)
    with batch_lock:
        sort_key = lambda x: x.file_size
        for post in sorted(posts, key=sort_key, reverse=True):
            if post.file_ext == 'webm' and False:
                print('found webm, skipping download')
            else:
                post.load_file(file_handler)
            index += 1

new_dimensions = (window.width, window.height)
new_thread(loadPage)
navigate_page.set(1)
init = True

@window.event
def on_draw():
    global init
    if init:
        init = False
        window.maximize()
    window.clear()
    with batch_lock:
        batch.draw()

    fps_display.draw()

moveEvent = threading.Event()
window_pos = (-1,-1)
nwindow_pos = (-1,-1)
@window.event
def on_move(x, y):
    global window_pos, nwindow_pos
    moveEvent.set()
    nwindow_pos = (x,y)

@window.event
def on_resize(width, height):
    global new_dimensions, window_pos, nwindow_pos
    dheight = height - new_dimensions[1]
    if moveEvent.is_set():
        if window_pos[1] != nwindow_pos[1]:
            nwindow_pos = (nwindow_pos[0], window_pos[1])
        window_pos = nwindow_pos
    else:
        window_pos = (window_pos[0], window_pos[1]+dheight)
    new_dimensions = (width, height)
    moveEvent.clear()
    update(0)

@window.event
def on_key_press(symbol, modifiers):
    global page, query
    if symbol == pyglet.window.key.RIGHT:
        navigate_page.set()
    if symbol == pyglet.window.key.LEFT:
        navigate_page.set(-1)
    if symbol == pyglet.window.key.DOWN:
        os.system('start explorer.exe ' + tempfile.gettempdir() + config.TEMP_SUBD_DIR)
    if symbol == pyglet.window.key.UP:
        query = input('Enter a search query: ')
        page = 0
        navigate_page.set()

def update(dt):
    global new_dimensions, batch_sprites, posts, column_width, row_height, row_width, window_pos, nwindow_pos
    if moveEvent.is_set():
        nwindow_pos = window_pos
    moveEvent.clear()
    width = tools.transition('resize_width', 500, new_dimensions[0], tools.SQRT)
    height = tools.transition('resize_height', 500, new_dimensions[1], tools.SQRT)
    x = window_pos[0] - tools.transition('move_x', 500, window_pos[0], tools.SQRT)
    y = window_pos[1] - tools.transition('move_y', 500, window_pos[1], tools.SQRT)
    with batch_lock:
        while not sprite_deletion.empty():
            sprite = sprite_deletion.get_nowait()
            if sprite != None:
                sprite.delete()
            batch_sprites.remove(sprite)
            del sprite
        while not post_image_queue.empty():
            post, image = post_image_queue.get_nowait()
            if not post in posts:
                post.clear_cache()
                continue
            index = posts.index(post)
            if not batch_sprites[index] == None:
                batch_sprites[index].delete()
                batch_sprites[index] = None
            batch_sprites[index] = pyglet.sprite.Sprite(img=image, batch=batch)
            scale = min(1, window.width / batch_sprites[index].width)
            scale *= min(1, window.height / (batch_sprites[index].height * scale))
            batch_sprites[index].scale = scale
        index = 0
        for post in posts:
            postMsg = post.message
            if postMsg != None:
                print(postMsg)
            column = post.column
            row = len(row_height) - 1 - post.row
            if not batch_sprites[index] == None:
                padding_x = 20 if column + 1 < len(column_width) else 0
                padding_y = 20 if row + 1 < len(row_height) else 0
                sprite = batch_sprites[index]
                sprite.x = sum(column_width[:column]) + (width - row_width[row])/2 + (column_width[column] - sprite.width - padding_x)/2 - x
                sprite.y = sum(row_height[:row]) + (height - sum(row_height))/2 + (row_height[row] - sprite.height - padding_y)/2 + y
            index += 1

pyglet.clock.schedule_interval(update, 1/60)
window.set_visible()
pyglet.app.run()

for sprite in batch_sprites:
    if not sprite == None:
        sprite.delete()
for post in posts:
    post.clear_cache()
program_stop.set()
for process in threads:
    process.join()