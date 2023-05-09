import time

from typing import  Callable, Any

class DelayedTask:
    def __init__(self, delay: float, cb: Callable[..., None], *args: Any, is_repetitive: bool = False) -> None:
        self._cb = cb
        self._args = args
        self._delay = delay
        self._start = time.perf_counter()
        self._is_active = True
        self._is_repetitive = is_repetitive

    def tick(self) -> bool:
        if (time.perf_counter() - self._start) > self._delay:
            if self._is_active:
                self._cb(*self._args)
                self._is_active = self._is_repetitive
            
            if self._is_active:
                self._start = time.perf_counter()
                
            return True
        
        return False
    
    def cancel(self) -> None:
        self._is_active = False
    
