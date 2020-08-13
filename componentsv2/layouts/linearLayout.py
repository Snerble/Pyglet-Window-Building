from . import Layout

class LinearLayoutArgs:
	def __init__(self):
		super().__init__()

class LinearLayout(Layout):
	def __init__(self, parent):
		super().__init__(parent)

		self.size.width.set_value(lambda : self.parent.size.width.value)
		self.size.width.observe(self.parent.size.width)

		self.size.width.invalidated += self._on_layout
		self.size.height.clear_observations()

		self._args = list()
	
	def _on_layout(self):
		"""Updates the layout information of the child components.
		"""
		offset = 0
		for child, _ in zip(self, self._args):
			# Set the width to match this layout
			child.size.width.set_value(self.size.width.value)
			# Set the y offset and increment the offset value with the height
			child.size.y.set_value(offset)
			offset += child.size.height.value
		self.size.height.set_value(offset)

	def add(self, component):
		super().add(component)
		self._args.append(LinearLayoutArgs())
		self._on_layout()

	def remove(self, component):
		self._args.pop(self.index(component))
		super().remove(component)
		self._on_layout()

	def draw(self):
		try:
			self._group.set_state()

			for child in self:
				child.draw()
			super().draw()
		finally:
			self._group.unset_state()