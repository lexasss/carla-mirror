import glob
import os
import sys

from typing import Optional

PACKAGE_EXT = 'egg'

def add_carla_path(path: Optional[str] = None) -> None:
    if path and path in sys.path:
        return

    if path is None:
        p = os.environ["VIRTUAL_ENV"].split('\\')
        i = p.index("PythonAPI") + 1
        p = p[:i]
        path = "/".join(p) + "/carla/dist"
            
    bin_version = 'win-amd64' if os.name == 'nt' else 'linux-x86_64'
    matched_carla_api = glob.glob(f'{path}/carla-*{sys.version_info.major}.{sys.version_info.minor}-{bin_version}.{PACKAGE_EXT}')
    #matched_carla_api = glob.glob(f'{path}/carla-*-cp{sys.version_info.major}{sys.version_info.minor}-{bin_version}.whl')

    if (len(matched_carla_api) == 0):
        carla_apis = glob.glob(f'{path}/carla-*-{bin_version}.{PACKAGE_EXT}')
        carla_apis = '\n  '.join(carla_apis)
        raise RuntimeError(f'you are running the script in Python {sys.version_info.major}.{sys.version_info.minor}, but these CARLA APIs support different Python versions:\n    {carla_apis}')
    
    sys.path.append(matched_carla_api[0])
