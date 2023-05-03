from typing import Callable, List, TypeVar, Generic

T = TypeVar("T")

class Event(Generic[T]):
 
    def __init__(self):
        self.__eventhandlers: List[Callable[..., None]] = []
 
    def __iadd__(self, handler: Callable[..., None]):
        self.__eventhandlers.append(handler)
        return self
 
    def __isub__(self, handler: Callable[..., None]):
        self.__eventhandlers.remove(handler)
        return self
 
    def __call__(self, *args: T, **keywargs: T):
        for eventhandler in self.__eventhandlers:
            eventhandler(*args, **keywargs)
