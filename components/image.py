from components import Component, RelativeConstraint, Polygon
from threading import Lock

import os.path
import pyglet
import asyncio
import tools

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
        super().__init__(parent, **kwargs)

        # Initialize members
        self._sprite = None
        self.__image = None
        self.__spriteGroup = ImageGroup(self, self._group)
        self.__file_path = None

        # Assign all properties
        self.fit_mode = kwargs.get('fit_mode', 'fit')
        self.align = kwargs.get('align', 'center')
        self.vertical_align = kwargs.get('vertical_align', 'center')
        self.async_image = kwargs.get("image")
        self.async_image = kwargs.get("async_image")

    @Component.width.setter
    def width(self, value):
        if value == "wrap_content":
            value = RelativeConstraint(
                lambda : self._sprite.width if not self._sprite == None else 0
            )
        Component.width.fset(self, value)
    
    @Component.height.setter
    def height(self, value):
        if value == "wrap_content":
            value = RelativeConstraint(
                lambda : self._sprite.height if not self._sprite == None else 0
            )
        Component.height.fset(self, value)

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
            value = os.path.expandvars(value)
            if os.path.splitext(value)[1].lower() == '.gif':
                self.__image = pyglet.image.load_animation(value)
            else:
                self.__image = pyglet.image.load(value)
            self.__file_path = os.path.abspath(value)
        else:
            self.__image = value
        
        # Create the new sprite
        self._sprite = pyglet.sprite.Sprite(self.__image)
        
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
            value = os.path.expandvars(value)
            if os.path.splitext(value)[1].lower() == '.gif':
                image = pyglet.image.load_animation(value)
            else:
                image = pyglet.image.load(value)
            self.__image_lock.release()
            self.__file_path = os.path.abspath(value)

        def setter():
            self.image = image
            self.draw()
        # Run the setter on the main thread
        pyglet.clock.schedule_once(lambda x : setter(), 0)

    def delete(self):
        """Deletes the current sprite (If one is loaded)."""
        self.__image = None
        if not self._sprite == None:
            self._sprite.delete()

    def invalidate(self):
        if self._sprite == None: return
        self.__spriteGroup.set_state()

    def draw(self):
        # TODO use set_state_recursive when the parent is still valid
        # Basically, if this component is invalid, it will have to
        # invoke the group hierarchy manually. If this component is
        # redrawn by it's parent, it does not need to recursively
        # set the state because it is already done by the parent.
        # TODO Steal java's invalidate thingy
        if self._sprite == None: return
        self.invalidate()
        self._group.set_state()

        self._sprite.draw()
        
        self.__spriteGroup.unset_state()
        self._group.unset_state()

class ImageGroup(pyglet.graphics.Group):
    """Custom group class that resizes the image to fit the parent Image component"""

    def __init__(self, rootComponent, parent=None, **kwargs):
        """Initializes a new instance of ImageGroup."""
        super().__init__(parent)
        self._root = rootComponent

    def set_state(self):
        sprite = self._root._sprite
        sprite.update(0, 0, None, 1, 1, 1)

        # Apply fit scaling
        fit_mode = self._root.fit_mode
        try:
            if fit_mode == 'fit': scaling = self.fit()
            elif fit_mode == 'fill': scaling = self.fill()
            elif fit_mode == 'stretch': scaling = self.stretch()
            else: raise NotImplementedError()
        except ZeroDivisionError: return

        sprite.update(None, None, None, *scaling)
        
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
        scale = self._root.width / sprite.width
        sprite.scale = scale
        scale *= self._root.height / sprite.height
        sprite.scale = scale

        # Redundant width scaling. This allows the width to grow with wrap_content
        scale *= min(self._root.width / sprite.width, 1)

        return scale, 1, 1

    def fill(self):
        """Scales the image to fill both width and height."""
        sprite = self._root._sprite

        # Calculate a scale that fits and never decreases the scale
        scale = self._root.width / sprite.width
        scale *= max(self._root.height / (sprite.height * scale), 1)
        
        return scale, 1, 1
    
    def stretch(self):
        """Scales the image's width and height seperately to fit both width and height.

        This does not preserve the aspect ratio."""
        sprite = self._root._sprite

        # Calculate a fitting scale per axis
        scale_x = self._root.width / sprite.width
        scale_y = self._root.height / sprite.height

        return 1, scale_x, scale_y