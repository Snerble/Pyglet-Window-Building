import pyglet
from typing import Any
from components import Component, RelativeConstraint, Constraint

class Layout(Component):
    def __init__(self, parent=None, **kwargs):
        kwargs.setdefault("width", "match_parent")
        kwargs.setdefault("height", "match_parent")

        super().__init__(parent, **kwargs)

        # Initialize members
        self._children = list()

    def add(self, component: Component):
        """Adds the specified component to this layout.
        
        Raises an error if the component is already present."""
        assert issubclass(type(component), Component), f"Component expected, but {type(component).__name__} was found."
        assert component not in self._children, "This component is already added to this layout."
        self._children.append(component)
    
    def remove(self, component: Component):
        """Removes the specified component from this layout.

        Raises ValueError if the component is not present."""
        self._children.remove(component)
    
    def __add__(self, value: Component) -> 'Layout':
        """Adds the component from this layout if the value is a Component object."""
        if issubclass(type(value), Component):
            self.add(value)
            return self
    
    def __sub__(self, value: Component) -> 'Layout':
        """Removes the component from this layout if the value is a Component object."""
        if issubclass(type(value), Component):
            self.add(value)
            return self

    def __contains__(self, value: Component) -> bool:
        """Returns whether the given component is present in this layout."""
        return value in self._children

    def __len__(self) -> int:
        return len(self._children)

    def draw(self):
        self._group.set_state()
        for c in (c for c in self._children if c.y + c.height >= 0 and c.y <= self.max_content_height):
            c.draw()
        self._group.unset_state()