import os

from typing import Any
from datetime import datetime

class Logger:
    date = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    file = open(f'logs/wide_{date}.txt', 'w')
    count = 0

    def __init__(self, type: str) -> None:
        self._type = type
        
        print(f'LOG: created "{type}" log')
        
        Logger.count += 1
        
    def __del__(self):
        print(f'LOG: deleted "{self._type}" log')
        Logger.count -= 1
        if Logger.count == 0:
            size = Logger.file.tell()
            Logger.file.close()
            
            if size == 0:
                os.remove(Logger.file.name) 
                
            print('LOG: file closed')
    
    def log(self, *params: Any) -> None:
        if Logger.file.closed:
            return
        
        timestamp = datetime.utcnow().timestamp()
        data = '\t'.join([str(x) for x in params])
        Logger.file.write(f'{timestamp}\t{self._type}\t{data}\n')
        
        print(f'LOG: {timestamp}\t{self._type}\t{data}')