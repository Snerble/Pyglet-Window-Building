# Ramblings and mental notes

## Problems
---
### Convoluted Cacheable syntax
Placing callbacks on the update events of cacheables is convoluted and tedious.

The following syntax:
```python
Component.max_width[self.parent] += Component.width.fdel, self
```
can be quite confusing, especially considering that intellisense does not provide useful suggestions for descriptor objects.

For event handlers that are always present *(e.g. width updates max_content_width)*, the use of additional function decorators should be possible. Internal relations such as the one between `width` and `max_content_width` could be configured as following:
```python
@Cacheable
def width(self):
    pass

@Cacheable(width) # This cache will clear if `width` changes
def max_content_width(self):
    pass
```
This however doesn't handle the events in a conventional way and instead must either wraps the decorated function in code that invokes the other Cacheable or it keeps track of a list these relations that is used in the `__get__` method of the Cacheable.

There is currently no easy way to create dynamic relations such as those required by `match_parent`. Due to their dynamic nature, all subscribed event handlers must be disposed of properly.his poses additional overhead when making complex relations such as `wrap_content`.

For layouts that are frequently reused such as scroll layouts, where many child components may be added or removed, a constraint like `wrap_content` requires each child component to notify the parent component of any changes. This means that because the `wrap_content` is specified in the parent, that parent must subscribe to the events of all child components.
<br>
In the event that a child component is reused, *(e.g. transferred from one scroll layout to another)* each of these events must be cleaned up as to not cause unexpected issues. Since the `wrap_content` text is lost once parsed by the property, use of callbacks is required to dynamically set up this cleaning step.

Preferrably, these relationships can easily be disposed together by simply starting the property setter with unsubscribing all events since unsubscribing events that were never subscribed raises no error. This is not straightforward however since this step must happen after the setter value has passed validation. Currently, new event handlers are subscribed before the assertions, so a boolean must be used to skip the unsubscribing step.

---
### Ideas regarding caching
It is possible to get the variables from a function's closure and use them. By using the opcodes in the `co_code` member you can figure out what exactly is being used. Therefore it is possible to assign an event to a Cacheable using just the code and closure of a function.

There are problems with this:
- It may not be possible to account for every referenced Component without either spending too much time resolving the code of the function or enumerating lists.

Alternatives such as passing all used Components as parameters to the RelativeConstraint also has drawbacks:
- Unlike with using `self.parent` in a lambda, passing `self.parent` as an argument will mean that the reference used by the lambda cannot change unless the argument is changed. This means that e.g. changing the parent component requires updating many RelativeConstraints because they all use an old reference.

Sometimes Cacheables may be used despite the fact that only the `on_change` event is required. Cacheable may need to be split into another class that represents only the event part of the Cacheable property.

# Unresolved Issues
- Parent components with `wrap_content` can cause issues when their child components have `match_parent`.

# TODOs
- Cacheables need a new `on_change` event and the current `on_change` should be renamed to `on_update`. The `on_change` is only called when the setter is invoked and it also invokes `on_update`. The `on_update` event is called whenever the setter or deleter is invoked.

- Events need an `addSingle` method for adding callback functions with a single use. Consider using an enum for callback flags.

- Cacheables should be 'castable' to an instance of a class. This means that when the following code is used: `Component.width[self]`, then all operations that require a reference object already have that filled in. This hopefully makes the syntax less confusing and puts emphasis on the idea that you are using the properties of an instance rather than the class.