import os
import glob
import sys

from contextlib import contextmanager
from typing import Generator

PACKAGE_EXT = 'egg'

def add_carla_path(path: str = '../carla/dist') -> None:
    if path in sys.path:
        return

    bin_version = 'win-amd64' if os.name == 'nt' else 'linux-x86_64'
    matched_carla_api = glob.glob(f'{path}/carla-*{sys.version_info.major}.{sys.version_info.minor}-{bin_version}.{PACKAGE_EXT}')
    #matched_carla_api = glob.glob(f'{path}/carla-*-cp{sys.version_info.major}{sys.version_info.minor}-{bin_version}.whl')

    if (len(matched_carla_api) == 0):
        carla_apis = glob.glob(f'{path}/carla-*-{bin_version}.{PACKAGE_EXT}')
        carla_apis = '\n  '.join(carla_apis)
        raise RuntimeError(f'you are running the script in Python {sys.version_info.major}.{sys.version_info.minor}, but these CARLA APIs support different Python versions:\n    {carla_apis}')
    
    sys.path.append(matched_carla_api[0])


@contextmanager         # allows using the function in 'with' statement
def suppress_stdout() -> Generator[None, None, None]:
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield       # here the body of the external 'with' statement is executed
        finally:
            sys.stdout = old_stdout
