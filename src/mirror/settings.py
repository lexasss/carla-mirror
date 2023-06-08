import os
import copy
import jsonpickle
import json
import uuid

from typing import Optional, Tuple, List, Any

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
    def create(section: str) -> Tuple['MirrorSettings', bool]:
        filename = os.path.join(FILENAME)
        mac = hex(uuid.getnode())
        try:
            with open(filename, mode='r') as f:
                json_data: Any = jsonpickle.decode(f.read())
                local_data = json_data[mac]
                section_data = local_data[section]
                return MirrorSettings(section, **section_data), True
                
        except:
            return MirrorSettings(section), False

    @staticmethod
    def save(settings: 'MirrorSettings'):
        filename = os.path.join(FILENAME)
        mac = hex(uuid.getnode())
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
        
        if mac in json_data:
            local_data = json_data[mac]
        else:
            local_data = json.loads('{}')
        
        try:
            local_data[settings._section] = copy.deepcopy(settings)
            
            keys: List[str] = []
            for key in local_data[settings._section].__dict__:
                keys.append(key)

            for key in keys:
                if key[0] == '_':
                    del local_data[settings._section].__dict__[key]
            
            json_data[mac] = local_data
            json_data: Any = jsonpickle.encode(json_data, unpicklable = False, indent = 2)
            
            with open(filename, mode='w') as f:
                f.write(json_data)
                
        except Exception as ex:
            print(ex)
