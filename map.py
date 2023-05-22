import argparse

from typing import Optional

from src.carla.utils import add_carla_path
add_carla_path()

from src.carla.environment import CarlaEnvironment

try:
    import carla
except ImportError:
    raise RuntimeError('cannot import CARLA')

class Settings:
    def __init__(self) -> None:
        args = self._make_args()
        
        self.map: Optional[str] = args.map
        self.host: str = args.host
        
    def _make_args(self):
        argparser = argparse.ArgumentParser(
            description='CARLA map')
        argparser.add_argument(
            '-m',
            '--map',
            default=None,
            help='Carla map ID')
        argparser.add_argument(
            '-h',
            '--host',
            default='localhost',
            help='Carla IP, or "localhost"')
        
        return argparser.parse_args()

if __name__ == '__main__':
    settings = Settings()
    
    if settings.map is None:
        print('Usage: python .\\map.py -m=MAP_ID')
        exit()

    client = carla.Client(settings.host, 2000)
    client.set_timeout(20.0)

    try:
        environment = CarlaEnvironment(client)
        world = environment.load_world(settings.map)

    except KeyboardInterrupt:
        print('Cancelled by user')
    except:
        print(f'CARLA is not running')
    
    else:    
        print('Done')
