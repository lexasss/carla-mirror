import logging
import queue
import asyncio, threading

from websockets.exceptions import ConnectionClosedOK
from websockets.server import serve, WebSocketServerProtocol
from typing import Callable, Set, Optional, cast

class WsServer:
    def __init__(self, cb: Callable[..., None]):
        self._isRunning = True
        self._cb = cb
        
        self._requests: queue.Queue[str] = queue.Queue()
        self._responses: queue.Queue[str] = queue.Queue()
        
        self._clients: Set[WebSocketServerProtocol] = set()
        
        self._thread = threading.Thread(target = self._start)
        self._thread.start()
        
    def close(self) -> None:
        self._isRunning = False
        self._thread.join()
        
    def send(self, msg: str) -> None:
        self._responses.put(msg)

    # Internal

    def _start(self) -> None:
        print('WSS: started')

        try:
            asyncio.run(self._run_server())
        except Exception:
            logging.exception('start: asyncio.run')

        print('WSS: closed')
        
    async def _client_connected(self, ws: WebSocketServerProtocol) -> None:
        print('WSS: client connected')
        
        self._clients.add(ws)
        
        while self._isRunning and not ws.closed:
            message: Optional[str] = None
            try:
                message = cast(str, await ws.recv())
            except ConnectionClosedOK:
                pass
            except:
                logging.exception('_client_connected: await ws.recv()')
        
            if message:
                self._requests.put(message)
                
        self._clients.discard(ws)
        
        print('WSS: client diconnected')
            
    async def _run_server(self) -> None:
        async with serve(self._client_connected, "localhost", 15555):
            while self._isRunning:

                while self._responses.qsize() > 0:
                    msg = self._responses.get()
                    for client in self._clients:
                        await client.send(msg)

                while self._requests.qsize() > 0:
                    try:
                        msg = self._requests.get()
                        self._cb(msg)
                    except:
                        pass
                    
                await asyncio.sleep(0.1)
