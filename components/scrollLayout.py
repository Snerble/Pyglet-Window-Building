import pyglet
import interface.xmlParser as xml
from math import sin, pi, sqrt
from components import Component, RelativeConstraint, Constraint

class ScrollLayout(Component):
    def __init__(self, parent=None, **kwargs):
        kwargs.setdefault("width", "match_parent")
        kwargs.setdefault("height", "match_parent")

        super().__init__(parent, **kwargs)

        self.__root_component = xml.parse("interface/layouts/scrollLayout.xml")
        self.__root_component.parent = self

        # Initialize members
        self.__scroll_speed = 0
        self.__scrolls = list()
        self.__padding_right = 0
        self._invalidated = False
        
        # Initialize properties
        self.scroll_position = 0
        self.step_size = kwargs.get("step_size", 100)
        self.smooth_scroll = kwargs.get("smooth_scroll", True)
        self.scroll_duration = kwargs.get("scroll_duration", 0.1)
        self.stacking_factor = kwargs.get("stacking_factor", 4)

        # Initialize cache
        self._max_component_width = None
        self._scrollbar_padding = None

    @property
    def scroll_position(self) -> (int, float):
        return self.__scroll_position
    @scroll_position.setter
    def scroll_position(self, value: (int, float, str)):
        if type(value) == str: value = float(value)
        if value < 0:
            self.__scrolls.clear()
            value = 0
        max_value = max(0, self.content_height - self.height)
        if value > max_value:
            self.__scrolls.clear()
            value = max_value
        self.__scroll_position = value

    @property
    def step_size(self) -> (int, float):
        return self.__step_size
    @step_size.setter
    def step_size(self, value: (int, float, str)):
        if type(value) == str: value = float(value)
        assert type(value) in (int, float), "Value must be int or float"
        self.__step_size = value
    
    @property
    def scroll_duration(self) -> (int, float):
        return self.__scroll_duration
    @scroll_duration.setter
    def scroll_duration(self, value: (int, float, str)):
        if type(value) == str: value = float(value)
        assert type(value) in (int, float), f"Int or float expected, but {type(value).__name__} found."
        self.__scroll_duration = value

    @property
    def smooth_scroll(self) -> bool:
        return self.__smooth_scroll
    @smooth_scroll.setter
    def smooth_scroll(self, value: (bool, str)):
        if type(value) == str: value = True if value.lower() == "true" else False
        assert type(value) == bool, f"Boolean expected, but {type(value).__name__} was given."
        self.__smooth_scroll = value

    @property
    def stacking_factor(self) -> (int, float):
        if self.__sc__scroll_stacking_factor == 0: return None
        return 1 / self.__scroll_stacking_factor
    @stacking_factor.setter
    def stacking_factor(self, value: (int, float, str, None)):
        """Specifies how many scrollwheel inputs need to be stacked before the
        scroll acceleration is multiplied by 2.

       Passing None disables the stacking effect.

        This requires smooth_scroll to be True."""
        # Handle special string values
        if type(value) == str:
            if value.lower() in ("null", "none"): value = None
            else: value = float(value)
        if value:
            assert type(value) in (int, float), f"Int or float expected, but {type(value).__name__} was given."
            assert value > 0, "Value may not be less than 0."
            self.__scroll_stacking_factor = 1 / value
        else: self.__scroll_stacking_factor = 0
        print(value)

    @property
    def content_width(self) -> (int, float):
        return max(c.width for c in self.__root_component._children)
    @property
    def content_height(self) -> (int, float):
        return sum(c.height for c in self.__root_component._children)

    @Component.padding_right.getter
    def padding_right(self):
        if not self._invalidated and self._scrollbar_padding == None:
            self._scrollbar_padding = 50 if self.height < self.content_height else 0

        return Component.padding_right.fget(self) + (self._scrollbar_padding if self._scrollbar_padding else 0)

    # @Component.max_content_width.getter
    # def max_content_width(self) -> float:
    #     if self._max_component_width == None:
    #         self._max_component_width = Component.max_content_width.fget(self)
            
    #         # Early return for when this variable is being reset by invalidation
    #         if self._invalidated: return

    #         self._max_component_width -= 10 if self.height < self.content_height else 0
    #     return self._max_component_width

    def add(self, component: Component):
        self.__root_component.add(component)
    
    def insert(self, index: int, component: Component):
        self.__root_component._children.insert(index, component)

    def remove(self, component: Component):
        self.__root_component._children.remove(component)

    def set_handlers(self, parent: Component):
        if parent == None:
            return
        if issubclass(type(parent), pyglet.window.Window):
            parent.set_handler("on_mouse_scroll", self.on_mouse_scroll)
        else:
            self.set_handlers(parent.parent)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if not self.contains(x, y): return

        distance = scroll_y * -self.step_size
        if not self.smooth_scroll:
            self.scroll_position += distance
            return

        if len(self.__scrolls) == 0:
            pyglet.clock.tick()
            pyglet.clock.schedule(self.update)
        
        self.__scrolls.append([
            self.scroll_duration*2, # Lifetime variable in seconds
            self.scroll_duration*2, # Duration in seconds
            distance / self.scroll_duration**2 # Acceleration in pixels/s^2
        ])

    def update(self, dt):
        fps = 1/60 # TODO replace local with a more static value somewhere else
        for scroll in self.__scrolls[:]:
            # Clamp the fps multiplier to the remaining acceleration and deceleration time
            if scroll[0] > scroll[1] / 2 and scroll[0] - scroll[1] / 2 < fps:
                fps = scroll[0] - scroll[1] / 2
            elif scroll[0] < fps:
                fps = scroll[0]


            scroll[0] -= fps
            if scroll[0] <= 0:
                self.__scrolls.remove(scroll)
                continue
            
            # Increment in the first half, decrement in the other half
            if scroll[0] >= scroll[1] / 2:
                self.__scroll_speed += scroll[2] * fps * len(self.__scrolls)**self.__scroll_stacking_factor
            else:
                self.__scroll_speed -= scroll[2] * fps * len(self.__scrolls)**self.__scroll_stacking_factor
        
        # Reset and unschedule if no scroll elements remain
        if len(self.__scrolls) == 0:
            pyglet.clock.unschedule(self.update)
            self.__scroll_speed = 0
            self.scrollcount = 0
            return

        self.scroll_position += self.__scroll_speed * fps

    def invalidate(self):
        """Invalidates this component and forces it to redraw."""
        self._invalidated = True

        # Reset cache
        self._scrollbar_padding = None

        # Recalculate content size
        for c in self.__root_component._children:
            c.invalidate()

        self._invalidated = False

        # Update cache
        self._scrollbar_padding = None
        self.padding_right

        # Update content size
        for c in self.__root_component._children:
            c.invalidate()

        # Update remaining properties
        self.scroll_position = self.scroll_position

    def draw(self):
        self.invalidate()
        self._group.set_state()

        # # pyglet.gl.glTranslatef(0, self.scroll_position, 0)
        # offset = -self.scroll_position
        # for c in self.__root_component._children:
        #     c.y = offset
        #     offset -= c.height
        #     # pyglet.gl.glTranslatef(0, -c.height, 0)
        offset = -self.scroll_position
        for c in self.__root_component._children:
            c.y = offset
            offset += c.height
        self.__root_component.draw()
        
        self.__padding_right = 0
        self._group.unset_state()
    