from typing import Callable, Optional

from src.net.ws_server import WsServer

class TaskScreenRequest:
    def __init__(self, req: str, param: Optional[str]) -> None:
        self.req = req
        self.param = param

class TaskScreenRequests:
    target_noticed = 'target'
    lane_change_evaluated = 'vehicle'

class TaskScreen:
    def __init__(self, cb: Optional[Callable[[TaskScreenRequest], None]] = None) -> None:
        self._server = WsServer(self._parse)
        self._cb = cb

    def set_callback(self, cb: Callable[[TaskScreenRequest], None]) -> None:
        self._cb = cb
        
    def close(self) -> None:
        self._server.close()
        
    def show_button(self) -> None:
        self._server.send('show:button:Done')
        
    def show_questionnaire(self) -> None:
        self._server.send('show:questionnaire')
        
    def hide_questionnaire(self) -> None:
        self._server.send('hide:questionnaire')
        
    def show_message(self, msg: str) -> None:
        self._server.send(f'show:message:{msg}')
        
    # Internal

    def _parse(self, msg: str) -> None:
        p = msg.split(':')
        req = p[0]
        param = p[1] if len(p) > 1 else None
        
        if self._cb:
            self._cb(TaskScreenRequest(req, param))
