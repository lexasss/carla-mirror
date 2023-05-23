# =============================================================================
# This script is to set the vechicle properties 
# if the main script is running remotely
# (CARLA's traffic manager cannot connect to CARLA from a remote PC)
# =============================================================================
import argparse
import time

from typing import Dict, cast

from src.carla.utils import add_carla_path
add_carla_path()

from src.carla.vehicle_factory import VehicleFactory

try:
    import carla
except ImportError:
    raise RuntimeError('cannot import CARLA')

class Settings:
    def __init__(self) -> None:
        args = self._make_args()
        
        self.name = args.name
        self.is_manual_mode = args.manual == True
        
    def _make_args(self):
        argparser = argparse.ArgumentParser(
            description='CARLA map')
        argparser.add_argument(
            '-n',
            '--name',
            default=None,
            help='Vehicle`s name without "vehicle." prefix')
        argparser.add_argument(
            '-m',
            '--manual',
            action='store_true',
            help='The flag to set the manual driving mode')
        
        return argparser.parse_args()

if __name__ == '__main__':
    settings = Settings()
    
    if settings.name is None:
        print('Usage: python .\\map.py -n=COMPANY.MODEL')
        print('(type --help to see all options)')
        exit()

    client = carla.Client('localhost', 2000)
    client.set_timeout(5.0)

    VehicleFactory.set_driving_mode(settings.is_manual_mode)
        
    try:
        factory = VehicleFactory(client)
        world = client.get_world()
        
        vehicles: Dict[int, carla.Vehicle] = dict()
        
        while True:
            time.sleep(2)
            
            all_cars = world.get_actors().filter('vehicle.*')
            if len(vehicles) == 0 and len(all_cars) == 1:
                ego_car = cast(carla.Vehicle, all_cars[0])
                factory.configure_ego_car(ego_car)
                vehicles[ego_car.id] = ego_car
                print(f'Ego car is {ego_car.type_id}')
                continue
                
            cars = [x for x in all_cars if x.id not in vehicles ]
            
            for car in cars:
                vehicle = cast(carla.Vehicle, car)
                vehicles[vehicle.id] = vehicle
                factory.configure_traffic_vehicle(vehicle)
                
                print(f'Added {vehicle.type_id}')
                
    except KeyboardInterrupt:
        print('Cancelled by user')
    except:
        print('CARLA is not running')
    else:    
        print('Done')
