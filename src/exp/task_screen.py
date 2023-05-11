import json

from typing import Callable, Optional, Union, List, Any
from types import SimpleNamespace

from src.net.ws_server import WsServer

class TaskScreenRequest:
    def __init__(self, json: Any) -> None:
        self.type: str = json.type
        self.data: Optional[Union[str, float, int, bool, List[str], List[int], List[float]]] = json.data

class TaskScreenRequests:
    questionnaire = 'questionnaire'
    target = 'target'

class TaskScreen:
    def __init__(self, cb: Optional[Callable[[TaskScreenRequest], None]] = None) -> None:
        self._server = WsServer(self._parse)
        self._cb = cb

    def set_callback(self, cb: Callable[[TaskScreenRequest], None]) -> None:
        self._cb = cb
        
    def close(self) -> None:
        self._server.close()
        
    def show_button(self, caption: str = 'Spawn next target') -> None:
        data = json.dumps({
            'target': 'button',
            'cmd': 'show',
            'param': caption
        })
        self._server.send(data)
        
    def hide_button(self) -> None:
        data = json.dumps({
            'target': 'button',
            'cmd': 'hide'
        })
        self._server.send(data)
        
    def show_questionnaire(self) -> None:
        data = json.dumps({
            'target': 'questionnaire',
            'cmd': 'show'
        })
        self._server.send(data)
        
    def hide_questionnaire(self) -> None:
        data = json.dumps({
            'target': 'questionnaire',
            'cmd': 'hide'
        })
        self._server.send(data)
        
    def show_message(self, msg: Union[str, List[str]]) -> None:
        data = json.dumps({
            'target': 'message',
            'cmd': 'show',
            'param': msg
        })
        self._server.send(data)
        
    # Internal

    def _parse(self, msg: str) -> None:
        req = TaskScreenRequest(json.loads(msg, object_hook = lambda d: SimpleNamespace(**d)))
        if self._cb:
            self._cb(req)
