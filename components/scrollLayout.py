import pyglet
import interface.xmlParser as xml
from math import sin, pi, sqrt, ceil
from components import Component, RelativeConstraint, Constraint

class ScrollLayout(Component):
    def __init__(self, parent=None, **kwargs):
        kwargs.setdefault("width", "match_parent")
        kwargs.setdefault("height", "match_parent")

        super().__init__(parent, **kwargs)

        self.__root_component = xml.parse("interface/layouts/scrollLayout.xml", self)
        self.__root_component.parent = self

        # Initialize members
        self.__scroll_destination = 0
        self.__scroll_speed = 0
        self.__scrolls = list()
        self.__padding_right = 0
        self._invalidated = False
        
        # Initialize properties
        self.scroll_position = 0
        self.step_size = kwargs.get("step_size", 100)
        self.smooth_scroll = kwargs.get("smooth_scroll", True)
        self.scroll_duration = kwargs.get("scroll_duration", 0.2)
        self.stacking_factor = kwargs.get("stacking_factor", None)
        self.scroll_rate = kwargs.get("scroll_rate", self.window.screen.get_mode().rate if self.window else 60)

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
        max_value = max(0, self.content_height - self.max_content_height)
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
        self.__scroll_duration = value / 2 # Divided by 2 because the scroll duration is primarily used this way

    @property
    def scroll_rate(self) -> (int, float):
        return round(1 / self.__scroll_rate, 10)
    @scroll_rate.setter
    def scroll_rate(self, value: (int, float, str)):
        if type(value) == str: value = float(value)
        assert type(value) in (int, float), f"Int or float expected, but {type(value).__name__} found."
        self.__scroll_rate = 1 / value

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
        if self.__scroll_stacking_factor == 0: return None
        return 1 / self.__scroll_stacking_factor
    @stacking_factor.setter
    def stacking_factor(self, value: (int, float, str, None)):
        """Specifies how many scrollwheel inputs need to be stacked before the
        scroll acceleration is multiplied by 2.

       Passing None, 'None', 'null' or 0 disables the stacking effect.

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

    @property
    def content_width(self) -> (int, float):
        return max(c.width for c in self.__root_component._children)
    @property
    def content_height(self) -> (int, float):
        return sum(c.height for c in self.__root_component._children)

    # @Component.padding_right.getter
    # def padding_right(self):
    #     if not self._invalidated and self._scrollbar_padding == None:
    #         self._scrollbar_padding = 50 if self.height < self.content_height else 0

    #     return Component.padding_right.fget(self) + (self._scrollbar_padding if self._scrollbar_padding else 0)

    def add(self, component: Component):
        self.__root_component.add(component)
    
    def insert(self, index: int, component: Component):
        self.__root_component._children.insert(index, component)

    def remove(self, component: Component):
        self.__root_component._children.remove(component)

    def set_handlers(self):
        self.parent.window.set_handler("on_mouse_scroll", self.on_mouse_scroll)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if not self.contains(x, y): return

        distance = scroll_y * -self.step_size
        if not self.smooth_scroll or int(scroll_y) != scroll_y:
            self.scroll_position += distance
            return

        if len(self.__scrolls) == 0:
            pyglet.clock.schedule_interval(self.update, self.__scroll_rate)
        
        self.__scrolls.append([
            self.scroll_duration*2, # Lifetime in seconds
            distance / self.scroll_duration ** 2 * (len(self.__scrolls) + 1) ** self.__scroll_stacking_factor, 10 # Acceleration in pixels/s^2
        ])
        self.scroll_destination += distance

    def update(self, dt):
        fps = min(dt, self.__scroll_rate)
        for scroll in self.__scrolls[:]:
            mult = fps
            if scroll[0] < fps:
                mult = scroll[0]
            # Handle case when the halfway point falls in between a single frame
            elif round(scroll[0], 12) > self.scroll_duration and scroll[0] - self.scroll_duration < fps:
                # Ratio of the amount if time spent accelerating vs decelerating
                accel_ratio = (scroll[0] - self.scroll_duration) / fps

                # Apply intermediate acceleration travel
                self.scroll_position += scroll[1] * (accel_ratio ** 2) * (fps ** 2)
                # Add the remaining acceleration
                self.__scroll_speed += scroll[1] * (accel_ratio - 0.5) * 2 * fps
                scroll[0] -= fps
                continue

            # Remove the scroll if it has expired
            scroll[0] -= fps
            if round(scroll[0], 12) <= 0:
                self.__scroll_speed -= scroll[1] * mult
                self.__scrolls.remove(scroll)
                continue

            # Increment in the first half, decrement in the other half
            if scroll[0] >= self.scroll_duration:
                self.__scroll_speed += scroll[1] * mult
            else:
                self.__scroll_speed -= scroll[1] * mult

        # Reset and unschedule if no scroll elements remain
        if len(self.__scrolls) == 0:
            pyglet.clock.unschedule(self.update)
            self.__scroll_speed = 0

            # Set the precise scroll destination to remove any potential discrepancies
            self.scroll_position = self.__scroll_destination
            self.__scroll_destination = self.scroll_position
            return

        self.scroll_position += self.__scroll_speed * fps

    def draw(self):
        self._group.set_state()

        offset = round(-self.scroll_position)
        for c in self.__root_component._children:
            c.y = offset
            offset += ceil(c.height)
        self.__root_component.draw()
        
        self._group.unset_state()
    