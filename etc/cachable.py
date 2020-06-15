from functools import wraps
from typing import Any

from etc.events import EventCollection

class Cacheable:
	"""A Property-like class that caches the output from it's getter.

	If the value is set or deleted, the cache is cleared.

	This class contains an event callback list for all instances with this property.
	
	Usage: 
	```
	Cachable.on_update[obj] += lambda : print("callback")
	```
	"""
	def __init__(self, func=None):
		"""Initializes a new instance of Cachable with the specified getter function."""
		self._cache = dict()
		self.__events = EventCollection()

		self.fset = None
		self.fdel = self.clear
		self.fget = self.getter(func).fget if func else None

	def __get__(self, obj, owner):
		if obj is None:
			return self
		if self.fget is None:
			raise AttributeError("Unreadable attribute")
		return self.fget(obj)

	def __set__(self, obj, value):
		if self.fset is None:
			raise AttributeError("Can't set attribute")
		return self.fset(obj, value)
	
	def __delete__(self, obj):
		if self.fdel is None:
			raise AttributeError("Can't delete attribute")
		return self.fdel(obj)

	def getter(self, func):
		"""Descriptor to change the getter on a cachable."""
		@wraps(func)
		def fget_wrapper(obj):
			if obj not in self._cache:
				print(f"Recalculating {func.__name__} for {type(obj).__name__}")
				self._cache[obj] = func(obj)
			else:
				print(f"Using cached {func.__name__} for {type(obj).__name__}")
			return self._cache[obj]
		
		copy = type(self)()
		copy.__dict__ = self.__dict__.copy()
		copy.fget = fget_wrapper
		return copy

	def setter(self, func):
		"""Descriptor to change the setter on a cachable."""
		@wraps(func)
		def fset_wrapper(obj, value):
			func(obj, value)
			if not value == self._cache.get(obj):
				self.clear(obj)

		copy = type(self)()
		copy.__dict__ = self.__dict__.copy()
		copy.fset = fset_wrapper
		return copy

	def deleter(self, func):
		"""Descriptor to change the deleter on a cachable."""
		@wraps(func)
		def fdel_wrapper(obj):
			func(obj)
			self.clear(obj)

		copy = type(self)()
		copy.__dict__ = self.__dict__.copy()
		copy.fdel = fdel_wrapper
		return copy
	
	def clear(self, obj: Any):
		"""Clears the cached value for this descriptor on the specified obj.
		
		This also notifies all on_change event handlers for this descriptor on the specified obj.
		"""
		self._cache.pop(obj, None)
		self.__events[obj]()

	def chain_update(self, src: Any, tgt: Any):
		"""Subscribes the `deleter` of the tgt object to the `on_update` on the src object.
		
		This clears the cache on the target object.
		"""
		self.on_update[src] += self.fdel, tgt
	
	def unchain_update(self, src: Any, tgt: Any):
		"""Unsubscribes the `deleter` of the tgt object from the `on_update` on the src object."""
		self.on_update[src] -= self.fdel, tgt

	@property
	def on_update(self):
		return self.__events