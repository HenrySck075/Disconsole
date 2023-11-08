from typing import Generic, TypeVar
from copy import deepcopy
_KT = TypeVar("_KT",contravariant=True)
_VT = TypeVar("_VT",contravariant=True)

class DefaultDict(dict, Generic[_KT,_VT]):
    def __init__(self, map, default:_VT = None):
        super().__init__(map)
        self.default_value = default

    def __getitem__(self, __key: _KT) -> _VT: # pyright: ignore
        try:
            return super().__getitem__(__key)
        except KeyError: 
            self[__key]=deepcopy(self.default_value)
            return super().__getitem__(__key)


class EventEmitter:
    def __init__(self) -> None:
        self.__frogbert = DefaultDict[str, list]({},[])

    def emit(self, event: str, *emit_params):
        for i in self.__frogbert[event]:
            i(*emit_params)

    def on(self, event: str, cb):
        self.__frogbert[event].append(cb)
