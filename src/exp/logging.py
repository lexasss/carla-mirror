import os

from io import TextIOWrapper
from typing import Optional, Any
from datetime import datetime

class LogFile:
    def __init__(self) -> None:
        self.name: str
        self.file: TextIOWrapper
        
        self._count = 0
        
    def create(self, prefix: Optional[str] = None, suffix: Optional[str] = None) -> bool:
        if self._count == 0:
            name = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
            if prefix is not None:
                name = f'{prefix}_{name}'
            if suffix is not None:
                name = f'{suffix}_{name}'
            
            self.name = name    
            self.file = open(f'logs/{name}.txt', 'w')
            
        self._count += 1
        
        return self._count == 1
    
    def close(self) -> bool:
        self._count -= 1
        
        if self._count == 0:
            size = self.file.tell()
            self.file.close()
            
            if size == 0:
                os.remove(self.file.name) 
                print(f'LOG: removed [{self.name}]')
            else:
                print(f'LOG: closed [{self.name}]')
                
        return self._count == 0
        

class BaseLogger:
    def __init__(self, logfile: LogFile, type: Optional[str] = None, is_verbal: bool = False) -> None:
        if self.__class__ == BaseLogger: 
            raise NotImplementedError("Abstract class can't be instantiated")

        self._logfile = logfile
        self._type = type
        self._is_verbal = is_verbal

        if self._type is not None:
            print(f'LOG: created "{type}" [{self._logfile.name}]')
            
        else:
            print(f'LOG: created [{self._logfile.name}]')

    def __del__(self):
        if self._type is not None:
            print(f'LOG: finalized "{self._type}" [{self._logfile.name}]')
        else:
            print(f'LOG: finalized [{self._logfile.name}]')
        
        self._logfile.close()
    
    def log(self, *params: Any) -> None:
        if self._logfile.file.closed:
            return
        
        timestamp = datetime.utcnow().timestamp()
        data = '\t'.join([str(x) for x in params])
        if self._type is not None:
            self._logfile.file.write(f'{timestamp}\t{self._type}\t{data}\n')
        else:
            self._logfile.file.write(f'{timestamp}\t{data}\n')
        
        if self._is_verbal:
            print(f'LOG: {timestamp}\t{self._type}\t{data}')
            
class EventLogger(BaseLogger):
    logfile = LogFile()
    
    def __new__(cls, type: Optional[str] = None) -> 'EventLogger':
        EventLogger.logfile.create('event')
        return super().__new__(cls)
    
    def __init__(self, type: Optional[str] = None) -> None:
        super().__init__(EventLogger.logfile, type, True)

class TrafficLogger(BaseLogger):
    logfile = LogFile()
    
    def __new__(cls) -> 'EventLogger':
        TrafficLogger.logfile.create('traffic')
        return super().__new__(cls)
    
    def __init__(self) -> None:
        super().__init__(TrafficLogger.logfile)
