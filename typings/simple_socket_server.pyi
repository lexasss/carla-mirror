import socket

from typing import Any
from event_bus import EventBus
from abc import ABCMeta
from dataclasses import dataclass

class _Singleton(ABCMeta): ...

@dataclass
class SimpleSocketServer(EventBus, metaclass=_Singleton):
    server_socket: socket.socket
    
    def __init__(self) -> None: ...
    def send(self, sock: Any, message: bytes) -> None: ...
    def run(self, host: str = '0.0.0.0', port: int = 6666, max_conn: int = 5) -> None: ...
