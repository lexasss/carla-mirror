from typing import Callable, Optional

from src.exp.server import Server
# from src.exp.event import Event

class Remote:
    REQUESTS = [
        'target',
        'vehicle'
    ]
    
    def __init__(self, cb: Callable[[str, Optional[str]], None]) -> None:
        self._server = Server(self._parse)

        self._cb = cb
        # self.vehicle_response = Event[str]()
        # self.target_response = Event[None]()

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
        
        self._cb(req, param)
