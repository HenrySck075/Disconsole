# what pro

from typing import Any, Callable

class ref:
    def __init__(self, obj) -> None:
        self._watchers:list[Callable[[Any,Any],None]] = [] #zZz
        self._value = obj

        def __setattr__(sel, name, value):
            self.__finana__(value)
            return sel.__setattr2__(name, value) # pyright: ignore

        setattr(self._value,"__setattr2__",self._value.__setattr__)
        setattr(self._value,"__setattr__",__setattr__)

    def __finana__(self, new):
        for i in self._watchers:
            i(self._value, new)
    @property
    def value(self):
        return self._value
    
    @value.setter 
    def value(self, a):
        self.__finana__(a)
        self._value = a

class reactive(dict):
    def __init__(self, obj: dict[str, Any]) -> None:
        self._watchers:list[Callable[[Any,Any],None]] = [] #zZz
        super().__init__({k:ref(obj[k]) for k in obj})

    def __setattr__(self, __name: str, __value: Any) -> None:
        for i in self._watchers:
            i(self, __value)
        return super().__setattr__(__name, __value)

def watch(r: ref | reactive, cb: Callable[[Any, Any],None]):
    r._watchers.append(cb)

def forEach(r: ref, i: Callable[[Any,int|str],None]):
    "Do not use `.append` or anything similar in the cb unless it's guarranteed to have new item appended"
    if hasattr(r.value, "__iter__") or hasattr(r.value, "__getitem__"):
        for idx,j in enumerate(r.value):
            i(j,idx)
    elif type(r.value) == dict:
        for k in r.value.keys():
            i(r.value[k],k)
    else: raise ValueError("Ref value is not iterable")

    def c(old,new):
        if type(old) != type(new): return
        if hasattr(new, "__iter__") or hasattr(new, "__getitem__"):
            for idx,j in enumerate(new):
                if j not in old:
                    i(j,idx)
                    break
    watch(r,c)
