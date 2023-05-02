from typing import Any
from datetime import datetime

class Logger:
    date = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    file = open(f'logs/wide_{date}.txt', 'w')
    count = 0

    def __init__(self, type: str) -> None:
        self._type = type
        print(f'Created "{type}" log')
        Logger.count += 1
        
    def __del__(self):
        print(f'Deleted "{self._type}" log')
        Logger.count -= 1
        if Logger.count == 0:
            Logger.file.close()
            print('Log file closed')
    
    def log(self, *params: Any):
        timestamp = datetime.utcnow().timestamp()
        data = '\t'.join([str(x) for x in params])
        Logger.file.write(f'{timestamp}\t{self._type}\t{data}\n')
        print(f'{timestamp}\t{self._type}\t{data}')