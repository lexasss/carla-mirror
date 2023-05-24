import os
import copy
import jsonpickle
import json

from typing import Optional, List, Any

FILENAME = 'mirror_settings.json'

class MirrorSettings:
    def __init__(self, section: str, **settings: Any) -> None:
        self.x = 0
        self.y = 0
        self.width: Optional[int] = None
        self.height: Optional[int] = None
        self.offset_x = 0
        self.offset_y = 0
        
        self._section = section
        self._is_initialized = False
        
        for key, val in settings.items():
            setattr(self, key, val)    
            self._is_initialized = True

    def is_initialized(self) -> bool:
        return self._is_initialized
    
    @staticmethod
    def create(section: str) -> 'MirrorSettings':
        filename = os.path.join(FILENAME)
        try:
            with open(filename, mode='r') as f:
                json_data: Any = jsonpickle.decode(f.read())
                section_data = json_data[section]
                return MirrorSettings(section, **section_data)
                
        except:
            return MirrorSettings(section)

    @staticmethod
    def save(settings: 'MirrorSettings'):
        filename = os.path.join(FILENAME)
        json_data = None
        
        try:
            with open(filename, mode='r') as f:
                json_data = json.loads(f.read())
                if json_data is None:
                    return
        except FileNotFoundError:
            pass

        if json_data is None:
            json_data = json.loads('{}')
        
        try:
            json_data[settings._section] = copy.deepcopy(settings)
            
            keys: List[str] = []
            for key in json_data[settings._section].__dict__:
                keys.append(key)

            for key in keys:
                if key[0] == '_':
                    del json_data[settings._section].__dict__[key]
            
            json_data: Any = jsonpickle.encode(json_data, unpicklable=False)
            
            with open(filename, mode='w') as f:
                f.write(json_data)
                
        except Exception as ex:
            print(ex)
