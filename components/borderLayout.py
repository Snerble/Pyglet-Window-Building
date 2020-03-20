import pyglet
from components import Component, RelativeConstraint

class BorderLayout(Component):
    """A component layout with 5 distinct component areas; North
    East, South, West and Center."""

    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3
    CENTER = 4

    # TODO replace hardcoded limit
    min_component_height = 50
    min_component_width = 50

    def __init__(self, parent=None, **kwargs):
        kwargs.setdefault("width", "match_parent")
        kwargs.setdefault("height", "match_parent")
        super().__init__(parent, **kwargs)

        # Initialize fields
        self._children = {
            BorderLayout.NORTH: None,
            BorderLayout.EAST: None,
            BorderLayout.SOUTH: None,
            BorderLayout.WEST: None,
            BorderLayout.CENTER: None
        }

    def add(self, component: Component, location: int):
        """Puts the specified component in the given location within this layout."""

        assert component is not None, "The value for 'component' may not be None."
        assert type(location) == int and location >= 0 and location < 5, "Invalid value for parameter 'location'."
        assert self._children[location] is None, "The given location already contains a component."

        self._children[location] = component

    def get(self, location: int):
        """Returns the component at the specified location."""
        assert type(location) == int and location >= 0 and location < 5, "Invalid value for parameter 'location'."
        return self._children[location]

    def remove(self, component: Component):
        """Removes the specified component from this layout."""

    @property
    def children(self):
        return self._children.values()

    def draw(self):
        self._group.set_state()

        for location, component in self._children:
            if component is None: continue

            if location == BorderLayout.NORTH:
                if component.height < self.min_component_height:
                    component.height = self.min_component_height
                elif component.height > self.height:
                    pass
                # TODO finish

        self._group.unset_state()

