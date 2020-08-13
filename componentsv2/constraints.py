from typing import Union, TypeVar, Generic, Callable, Set, Dict, Any
from threading import Lock

from etc.events import Event

__all__ = [
	'Value',
	'Cacheable'
]

T = TypeVar('T')

class Value(Generic[T]):
	def __init__(self, value: Union[Callable[[], T], T], **kwargs: Dict[str, Any]):
		self.name = kwargs.get("name") or type(self).__name__
		
		self.__value_lock = Lock()
		self.set_value(value)

	@property
	def value(self) -> T:
		"""Gets the value held by this Value instance."""
		return self.get_value()

	def get_value(self) -> T:
		"""Returns the value held by this Value instance."""
		with (self.__value_lock):
			if (callable(self.__value)):
				return self.__value()
			return self.__value

	def set_value(self, value: Union[Callable[[], T], T]):
		"""Sets the value of this Value instance.

		`value` may be an object of type T or a Callable with a return type of T.
		"""
		with (self.__value_lock):
			self.__value = value

	def __str__(self) -> str:
		return str(self.value)

	def __repr__(self) -> str:
		return f"<{self.name}: {repr(self.value)}>"

class Cacheable(Value[T]):
	def __init__(self, value: Union[Callable[[], T], T], pre_cache = False, **kwargs: Dict[str, Any]):
		self.__cache_lock = Lock()
		self.__cache: T = None
		self.__cached = False
		self.__invalidated = Event()

		self.__observer_lock = Lock()
		self.__observing_lock = Lock()
		self.__observing: Set['Cacheable'] = set()
		self.__observers: Set['Cacheable'] = set()

		super().__init__(value)

		# Initialize the cache if pre_cache is True
		if (pre_cache):
			self.get_value()
	
	def get_value(self) -> T:
		"""Returns the value held by this Cacheable instance, or a cached copy of
		a previously returned value."""
		with (self.__cache_lock):
			if (not self.__cached):
				self.__cache = super().get_value()
				self.__cached = True
			return self.__cache
	
	def set_value(self, value: Union[Callable[[], T], T]):
		"""Sets the value of this Cacheable and invalidates the cache.

		If the new value matches the cached value, the invalidation step is skipped.
		
		`value` may be an object of type T or a Callable with a return type of T.
		"""
		super().set_value(value)

		with (self.__cache_lock):
			should_invalidate = self.__cache != value
		if (should_invalidate):
			self.invalidate()

	def observe(self, other: 'Cacheable'):
		"""Adds this Cacheable to the observer list of the `other` Cacheable.
		
		This has no effect if this Cacheable is already observing the `other`
		Cacheable.

		Any subsequent calls to `invalidate()` to the `other` Cacheable will
		also invalidate this Cacheable.
		
		Use this if this Cacheable's callable relies on the `other` Cacheable.
		"""
		if (other is not None):
			with (self.__observing_lock):
				other.__add_observer(self)
				self.__observing.add(other)
	
	def undo_observe(self, other: 'Cacheable'):
		"""Removes this Cacheable from the observer list of the `other` Cacheable."""
		other.__remove_observer(self)

	def clear_observations(self):
		"""Removes all observations to other Cacheables that have been made by
		this Cacheable.
		"""
		with (self.__observing_lock):
			for other in self.__observing:
				other.__remove_observer(self)
			self.__observing.clear()

	def __add_observer(self, observer: 'Cacheable'):
		"""Adds the given Cacheable to this Cacheable's observer list."""
		with (self.__observer_lock):
			self.__observers.add(observer)

	def __remove_observer(self, observer: 'Cacheable'):
		"""Removes the given Cacheable from this Cacheable's observer list.
		
		No error is raised if the given Cacheable isn't in the observer list.
		"""
		with (self.__observer_lock):
			self.__observers.discard(observer)

	def __repr__(self):
		return f"{self.name}<{self.__cache}>" if self.__cached else f"{self.name}<...>"

	invalidated: Event = property(lambda self : self.__invalidated, fset = lambda self, value : None)

	# TODO Implement an invalidation logger
	LOG_INVALIDATIONS = True
	invalidations = 0

	def invalidate(self):
		"""Disposes the cached value and forces it to be recalculated
		during the next call to `get_value()`."""
		with (self.__cache_lock):
			self.__cache = None
			self.__cached = False
		
		self.invalidated()

		# Clone the observer set in a locked scope
		with (self.__observer_lock):
			observers = self.__observers.copy()
		
		if (len(observers) != 0):
			Cacheable.invalidations += len(observers)
		
		# Invalidate all observing cacheables
		for observer in observers:
			observer.invalidate()

class OffsettableCacheable(Cacheable[T]):
	def __init__(self, value: Union[Callable[[], T], T], offsetter: Union[Callable[[], T], T], pre_cache = False):
		super().__init__(value, pre_cache)

		self.__offset_lock = Lock()
		self.__offset = offsetter
	
	def get_value(self):
		v = super().get_value()
		return v + self.get_offset()

	def get_offset(self) -> T:
		with (self.__offset_lock):
			if (callable(self.__offset)):
				return self.__offset()
			return self.__offset

	def set_offset(self, offset: Union[Callable[[], T], T]):
		with (self.__offset_lock):
			self.__offset = offset