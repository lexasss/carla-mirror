from typing import Optional
from event_bus import EventBus

class SimpleSocketClient(EventBus):
    def __init__(self, host: str, port: int) -> None: ...
    def connect(self, timeout: Optional[float] = None) -> None: ...
    def disconnect(self) -> None: ...
    def send(self, message: bytes) -> None: ...
    def ask(self, message: bytes, timeout: float = 1.) -> Optional[bytes]: ...
