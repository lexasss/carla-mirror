import asyncio

from src.server import Server

class Remote:
    def __init__(self) -> None:
        self._server = Server(self._parse)

    def close(self):
        self._server.close()
        
    def _parse(self, msg: str):
        task = asyncio.create_task(self._echo('--' + msg + '--'))
        asyncio.get_event_loop().run_until_complete(task)
        
    async def _echo(self, msg: str):
        await asyncio.sleep(0.5)
        self._server.send(msg)
    