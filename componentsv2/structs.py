from typing import TypeVar, Generic, Union, Dict, Any
from .constraints import Value, Cacheable

TX = TypeVar('TX')
TY = TypeVar('TY')
TW = TypeVar('TW')
TH = TypeVar('TH')

class Size(Generic[TX, TY, TW, TH]):
	def __init__(self,
			x: Union[TX, Value[TX]],
			y: Union[TY, Value[TY]],
			width: Union[TW, Value[TW]],
			height: Union[TH, Value[TH]]
			):
		self.__x: Value[TX] = x if isinstance(x, Value) else Value(x)
		self.__y: Value[TY] = y if isinstance(y, Value) else Value(y)
		self.__width: Value[TW] = width if isinstance(width, Value) else Value(width)
		self.__height: Value[TH] = height if isinstance(height, Value) else Value(height)
	
	@property
	def x(self):
		return self.__x
	
	@property
	def y(self):
		return self.__y - self.__height
	
	@property
	def width(self):
		return self.__width
	
	@property
	def height(self):
		return self.__height

class CacheableSize(Generic[TX, TY, TW, TH]):
	def __init__(self,
			x: Union[TX, Cacheable[TX]],
			y: Union[TY, Cacheable[TY]],
			width: Union[TW, Cacheable[TW]],
			height: Union[TH, Cacheable[TH]],
			**kwargs: Dict[str, Any]):
		self.__x: Cacheable[TX] = x if isinstance(x, Cacheable) else Cacheable(x, name="x")
		self.__y: Cacheable[TY] = y if isinstance(y, Cacheable) else Cacheable(y, name="y")
		self.__width: Cacheable[TW] = width if isinstance(width, Cacheable) else Cacheable(width, name="width")
		self.__height: Cacheable[TH] = height if isinstance(height, Cacheable) else Cacheable(height, name="height")

		for value in (self.__x, self.__y, self.__width, self.__height):
			value.name = (kwargs.get("name") or type(self).__name__) + '.' + value.name

	@property
	def x(self):
		return self.__x
	
	@property
	def y(self):
		return self.__y
	
	@property
	def width(self):
		return self.__width
	
	@property
	def height(self):
		return self.__height

	def contains(self, x: float, y: float) -> bool:
		left = self.x.value + self.width.value
		bottom = self.y.value + self.height.value
		return self.x.value <= x and x < left and self.y.value <= y and y < bottom 
	
	def invalidate(self):
		"""Invalidates all Cached values of this CacheableSize."""
		for value in (self.__x, self.__y, self.__width, self.__height):
			value.invalidate()

	def __str__(self):
		return f"(x:{self.x}, y:{self.y}, w:{self.width}, h:{self.height})"