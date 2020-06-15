import asyncio
import io
import os.path
from threading import Lock, Thread
from urllib.parse import urlparse

import pyglet
from pyglet import gl
import ctypes
import requests

import tools
from components import Component, Polygon, RelativeConstraint

class Image(Component):
    # Lock to prevent errors during async image loading
    __image_lock: Lock = Lock()

    def __init__(self, parent=None, **kwargs):
        """Initializes a new instance of Image.

        Args:
            image -> See Image.setImage().
            width:
                int | float    -> An absolute value.
                Constraint     -> A constraint proxy for a value.
                'wrap_content' -> Equal to the loaded image width.
            height:
                int | float    -> An absolute value.
                Constraint     -> A constraint proxy for a value.
                'wrap_content' -> Equal to the loaded image height.

        Kwargs:
            batch:          The pyglet.graphics.Batch to draw this image to.
            image:          See Image.image
            fit_mode:       See Image.fit_mode
            align:          See Image.align.
            vertical_align: See Image.vertical_align
        """

        # Initialize members
        # self._component_graphics = None # TODO remove, the image's textures can simply be changed
        self._component_graphics = pyglet.image.Texture.create(1, 1)

        self._sprite_invalidated = False
        self._sprite = None
        self.__image = None
        
        super().__init__(parent, **kwargs)

        self.__spriteGroup = ImageGroup(self, self._group)
        self.__file_path = None

        # Assign all properties
        self.fit_mode = kwargs.get('fit_mode', 'fit')
        self.align = kwargs.get('align', 'center')
        self.vertical_align = kwargs.get('vertical_align', 'center')
        self.image = kwargs.get("image")

        self.set_value_watcher(self, self.invalidate, "max_content_width")
        self.set_value_watcher(self, self.invalidate, "max_content_height")

    @Component.width.setter
    def width(self, value):
        if value == "wrap_content":
            value = RelativeConstraint(lambda : self.content_width)
            # Add watcher that clears the width if the content changes
            self.set_value_watcher(self, "width", "content_width")
        else:
            # Remove watcher that clears the width if the content changes
            self.remove_value_watcher(self, "width", "content_width")

        Component.width.fset(self, value)
    
    @Component.height.setter
    def height(self, value):
        if value == "wrap_content":
            value = RelativeConstraint(lambda : self.content_height)
            # Add watcher that clears the height if the content changes
            self.set_value_watcher(self, "height", "content_height")
        else:
            # Add watcher that invalidates the image if the size changes
            self.remove_value_watcher(self, "height", "content_height")

        Component.height.fset(self, value)
    
    @Component.max_width.setter
    def max_width(self, value):
        if value == "wrap_content":
            def getter():
                return ((self.image.width
                    if issubclass(type(self.image), pyglet.image.AbstractImage)
                    else self.image.frames[0].image.width
                    if self.image and not len(self.image.frames) == 0
                    else 0) + self.padding_left + self.padding_right)
            value = RelativeConstraint(getter)
            # Add watcher that clears the max_width if the content changes
            self.set_value_watcher(self, "max_width", "content_width")
        else:
            # Add watcher that invalidates the image if the size changes
            self.remove_value_watcher(self, "max_width", "content_width")

        Component.max_width.fset(self, value)
    
    @Component.max_height.setter
    def max_height(self, value):
        if value == "wrap_content":
            def getter():
                return ((self.image.height
                    if issubclass(type(self.image), pyglet.image.AbstractImage)
                    else self.image.frames[0].image.height
                    if self.image and not len(self.image.frames) == 0
                    else 0))# + self.padding_top + self.padding_bottom)
            value = RelativeConstraint(getter)
            # Add watcher that clears the max_height if the content changes
            self.set_value_watcher(self, "max_height", "content_height")
        else:
            # Add watcher that invalidates the image if the size changes
            self.remove_value_watcher(self, "max_height", "content_height")

        Component.max_height.fset(self, value)

    @property
    def file_path(self):
        return self.__file_path

    @property
    def image(self) -> pyglet.image.AbstractImage:
        return self.__image
    @image.setter
    def image(self, value: (pyglet.image.AbstractImage, str)):
        """Disposes of previous resources and sets a new image.
        
        Args:
            image:
                AbstractImage | Animation -> An AbstractImage to use.
                str -> A path to an image to load.
        """
        if value == None: return
        assert type(value) in (pyglet.image.Animation, str) or issubclass(type(value), pyglet.image.AbstractImage)

        self.__file_path = None

        # Delete the previous sprite
        if not self._sprite == None:
            self._sprite.delete()

        # Load the image
        if type(value) == str:
            # Check if the value is a url
            file = None
            url = urlparse(value)
            if url.scheme in ("http", "https"):
                # Get byte stream from http response
                response = requests.get(value, stream=True)
                response.raise_for_status()
                file = io.BytesIO(response.content)
            else:
                value = os.path.abspath(os.path.expandvars(value))
            
            # Load the image
            self.__image = (pyglet.image.load_animation(value, file)
                if os.path.splitext(value)[1].lower() == '.gif'
                else pyglet.image.load(value, file))

            # Remember the file path
            self.__file_path = value
        else:
            self.__image = value
        
        # Create the new sprite
        # self._sprite = pyglet.sprite.Sprite(self.__image)
        self.invalidate()
        del self.content_width
        del self.content_height
        
    @property
    def fit_mode(self) -> str:
        return self.__fit_mode
    @fit_mode.setter
    def fit_mode(self, value: str):
        """Sets the way that the image is fitted in this component.
        
        Value:
            'fill'    -> Scales the image to fill this component.
            'fit'     -> Scales the image to fit both width and height.
            'stretch' -> Stretches the image in both x and y to fit.
        """
        assert value in ('fit', 'fill', 'stretch')
        self.__fit_mode = value

    @property
    def align(self) -> str:
        return self.__align
    @align.setter
    def align(self, value: str):
        """Sets the horizontal alignment of this image.
        
        Value:
            'left'   -> Displays the image on the left.
            'right'  -> Displays the image on the right.
            'center' -> Displays the image in the center.
        """
        assert value in ('left', 'right', 'center')
        self.__align = value

    @property
    def vertical_align(self) -> str:
        return self.__vertical_align
    @vertical_align.setter
    def vertical_align(self, value: str):
        """Sets the vertical alignment of this image.
        
        Value:
            'top'    -> Displays the image at the top.
            'bottom' -> Displays the image at the bottom.
            'center' -> Displays the image in the center.
        """
        assert value in ('top', 'bottom', 'center')
        self.__vertical_align = value

    @tools.runAsNewThread()
    def set_image(self, image):
        """Sets this components image on a fire-and-forget thread."""
        self.set_image_async(image)
    def set_image_async(self, value):
        """Asynchronous coroutine for setting this components image."""
        if value == None: return

        self.__file_path = None
        
        # Load the image
        if type(value) == str:
            self.__image_lock.acquire()

            # Check if the value is a url
            file = None
            url = urlparse(value)
            if url.scheme in ("http", "https"):
                # Get byte stream from http response
                response = requests.get(value, stream=True)
                response.raise_for_status()
                file = io.BytesIO(response.content)
            else:
                value = os.path.abspath(os.path.expandvars(value))
                
            self.__image = (pyglet.image.load_animation(value, file)
                if os.path.splitext(value)[1].lower() == '.gif'
                else pyglet.image.load(value, file))

            # Remember the file path
            self.__file_path = value
            self.__image_lock.release()
        else:
            self.__image = value

        self.invalidate()
        del self.content_width
        del self.content_height

    def delete(self):
        """Deletes the current sprite (If one is loaded)."""
        self.__image = None
        if not self._sprite == None:
            self._sprite.delete()

    @property
    def content_width(self) -> float:
        return (self._sprite.width
            if self._sprite
            else self.image.width
            if issubclass(type(self.image), pyglet.image.AbstractImage)
            else self.image.frames[0].image.width
            if self.image and not len(self.image.frames) == 0
            else 0) + self.padding_left + self.padding_right
    @content_width.deleter
    def content_width(self):
        pass
    
    @property
    def content_height(self) -> float:
        return (self._sprite.height
            if self._sprite
            else self.image.height
            if issubclass(type(self.image), pyglet.image.AbstractImage)
            else self.image.frames[0].image.height
            if self.image and not len(self.image.frames) == 0
            else 0) + self.padding_top + self.padding_bottom
    @content_height.deleter
    def content_height(self):
        pass

    def invalidate(self):
        self._sprite_invalidated = True

    def draw(self):
        if not self.visible or not self.image: return

        if self._sprite_invalidated:
            if not self._sprite:
                self._sprite_invalidated = False

                def getTexture(dt):
                    self._sprite = pyglet.sprite.Sprite(self.__image)
                    self.__spriteGroup.set_state()
                    self.invalidate()
                    # pyglet.clock.unschedule(getTexture)
                
                pyglet.clock.schedule_once(getTexture, 0)
            else:
                self.__spriteGroup.set_state()
                self._sprite_invalidated = False
                del self._component_graphics
                self._component_graphics = pyglet.image.Texture.create(int(self.max_content_width), int(self.max_content_height))
        
        if not self._sprite: return

        gl.glBindFramebuffer(pyglet.gl.GL_FRAMEBUFFER, 1)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self._component_graphics.id, 0)
        gl.glViewport(0, 0, round(self.max_content_width) + 1, round(self.max_content_height) + 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glOrtho(0, self.max_content_width / self.window.width * 2, 0, self.max_content_height / self.window.height * 2, -1, 1)
        self._sprite.draw()
        gl.glPopMatrix()

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glViewport(0, 0, self.window.width, self.window.height)

        gl.glClear(0)
            
        self._group.set_state()
        if False:
            self._sprite.draw()
        else:
            self._component_graphics.blit(0,0)
        self._group.unset_state()

class ImageGroup(pyglet.graphics.Group):
    """Custom group class that resizes the image to fit the parent Image component"""

    def __init__(self, rootComponent, parent=None, **kwargs):
        """Initializes a new instance of ImageGroup."""
        super().__init__(parent)
        self._root: Image = rootComponent

    def set_state(self):
        sprite = self._root._sprite
        sprite.update(0, 0, None, 1, 1, 1)
        del self._root.content_width
        del self._root.content_height

        # Apply fit scaling
        fit_mode = self._root.fit_mode
        try:
            if fit_mode == 'fit': scaling = self.fit()
            elif fit_mode == 'fill': scaling = self.fill()
            elif fit_mode == 'stretch': scaling = self.stretch()
            else: raise NotImplementedError()
        except ZeroDivisionError: return

        sprite.update(None, None, None, *scaling)
        del self._root.content_width
        del self._root.content_height
        
        # Apply horizontal align
        align = self._root.align
        if align == 'left': x = 0
        elif align == 'center': x = (self._root.max_content_width - sprite.width) / 2
        elif align == 'right': x = self._root.max_content_width - sprite.width
        else: raise NotImplementedError()

        # Apply vertical align
        vertical_align = self._root.vertical_align
        if vertical_align == 'bottom': y = 0
        elif vertical_align == 'center': y = (self._root.max_content_height - sprite.height) / 2
        elif vertical_align == 'top': y = self._root.max_content_height - sprite.height
        else: raise NotImplementedError()

        sprite.update(x, y)

    def fit(self):
        """Scales the image to fit both width and height."""
        sprite = self._root._sprite

        # Calculate a scale that fits
        sprite.scale = self._root.max_content_width / sprite.width
        # del self._root.content_height
        sprite.scale *= self._root.max_content_height / sprite.height
        # del self._root.content_width

        # Redundant width scaling. This allows the width to grow with wrap_content
        sprite.scale *= min(self._root.max_content_width / sprite.width, 1)

        return None, 1, 1

    def fill(self):
        """Scales the image to fill both width and height."""
        sprite = self._root._sprite

        # Calculate a scale that fits and never decreases the scale
        scale = self._root.max_content_width / sprite.width
        scale *= max(self._root.max_content_height / (sprite.height * scale), 1)
        
        return scale, 1, 1
    
    def stretch(self):
        """Scales the image's width and height seperately to fit both width and height.

        This does not preserve the aspect ratio."""
        sprite = self._root._sprite

        # Calculate a fitting scale per axis
        scale_x = self._root.max_content_width / sprite.width
        scale_y = self._root.max_content_height / sprite.height

        return 1, scale_x, scale_y
