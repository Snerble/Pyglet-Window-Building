from typing import Any, Dict, Union, Optional, List, Tuple, Set, Iterator

class Event:
	"""Event class that allows callback subscription and invocation.

	Usage:
	```
		def callback(*args):
			print("callback")

		event = Event()
		# Subscribe callback with and without arguments
		event += callback
		event += callback, 1, 2, 3

		# Invoke callback(s) using __call__() and invoke()
		event()
		event.invoke()

		# Unsubscribe callback
		event -= callback
	```

	The callback signiature depends on the parameters passed to the `invoke(...)` method.
	"""
	def __init__(self):
		"""Initializes a new instance of Event."""
		self.__event_handlers: List[Tuple['function', Any]] = list()

	def __call__(self, *args, **kwargs):
		self.invoke(*args, **kwargs)

	def invoke(self, *args, **kwargs):
		"""Invokes all subscribed callbacks with the specified args and kwargs."""
		for handler in self.__event_handlers:
			handler[0](*handler[1], *args, **kwargs)

	def __add__(self, func: Union[Tuple['function', Any], 'function']) -> 'Event':
		if isinstance(func, tuple):
			assert len(func) > 0 and callable(func[0]), "The tuple must begin with a function."
			self.__event_handlers.append((func[0], func[1:]))
		else:
			self.__event_handlers.append((func, tuple()))
		return self
	
	def __sub__(self, func: Union[Tuple['function', Any], 'function']) -> 'Event':
		if func in self.__event_handlers:
			self.__event_handlers.remove(func)
		return self

class EventCollection:
	"""Specialized dictionary class for containing multiple Events."""
	def __init__(self, **kwargs: Dict[Any, Event]):
		"""Initializes a new instance of EventCollection.

		kwargs: Optional dictionary to initialize this EventCollection with. Must contain
		only Events as values.
		"""
		assert False not in (isinstance(_, Event) for _ in kwargs.values()), "Kwargs may only contain event values."
		self.__events = kwargs
	
	def get(self, key: Any, default: Optional = None) -> Union[Event, Any]:
		"""Return the Event for key if key is in the collection, else default."""
		return self.__events.get(key, Optional)

	def pop(self, key: Any, default: Optional = None) -> Union[Event, Any]:
		"""Remove the specified key and return the corresponding Event. If key is not found,
		default is returned if given, otherwise KeyError is raised"""
		return self.__events.pop(key, default)

	def keys(self) -> Set[Any]:
		"""Returns a set-like object providing a view on this collection's keys."""
		return self.__events.keys()
	
	def values(self) -> List[Event]:
		"""Returns an object providing a view on this collection's values."""
		return self.__events.values()

	def items(self) -> Set[Tuple[Any, Event]]:
		"""Returns a set-like object providing a view on this collection's items."""
		return self.__events.items()

	def clear(self):
		"""Removes all items from this collection."""
		self.__events.clear()

	def __contains__(self, key: Any) -> bool:
		return key in self.__events.keys()

	def __getitem__(self, key: Any) -> Event:
		if key not in self:
			self.__events[key] = Event()
		return self.__events[key]
	
	def __setitem__(self, key: Any, value: Event):
		assert isinstance(value, Event), "Value must be an Event."
		self.__events[key] = value

	def __len__(self) -> int:
		return len(self.__events)

	def __iter__(self) -> Iterator:
		return self.__events.__iter__()

	def __repr__(self) -> str:
		return f"{type(self).__name__}<{len(self)}>"
