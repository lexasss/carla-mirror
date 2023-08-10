import socket

from typing import Optional, Any

from src.settings import Settings

from src.exp.scenario import Scenario
from src.exp.mirror_status import MirrorStatus
from src.exp.task_screen import TaskScreen

from src.net.tcp_server import TcpServer
from src.net.tcp_client import TcpClient

class ScenarioEnvironment(object):
    def __init__(self, is_primary_mirror: bool = True):
        self._is_primary_mirror = is_primary_mirror
        
        self._task_screen: Optional[TaskScreen] = None
        self._tcp_server: Optional[TcpServer] = None
        self._tcp_client: Optional[TcpClient] = None
        
        self.scenario: Optional[Scenario] = None
        self.mirror_status = MirrorStatus()
        
    def __enter__(self):
        settings = Settings()
        server_host = settings.primary_mirror_host

        is_tcp_server_running = TcpClient.can_connect(server_host)
        if is_tcp_server_running:
            self._is_primary_mirror = False

        if self._is_primary_mirror:
            try:
                self._tcp_server = TcpServer()
                self._tcp_server.start()
            except socket.error:
                self._is_primary_mirror = False
                self._tcp_server = None
            else:
                self._task_screen = TaskScreen()
                self.scenario = Scenario(self._task_screen, self._tcp_server, self.mirror_status) if self._task_screen else None
                
        if not self._is_primary_mirror:
            self._tcp_client = TcpClient(server_host)
            self._tcp_client.connect(self.mirror_status.handle_net_request)
            
        return self
    
    def __exit__(self, *args: Any):
        if self._task_screen:
            self._task_screen.close()
        if self._tcp_server:
            self._tcp_server.close()
        if self._tcp_client:
            self._tcp_client.close()
            
        return self
