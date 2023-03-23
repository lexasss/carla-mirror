import math
import random
import carla

from vehicle_factory import VehicleFactory
from settings import Settings
from typing import Callable, Optional

class Environment:
    FPS = 30
    
    def __init__(self,
                 client: carla.Client,
                 settings: Settings) -> None:
        self.client = client
        self.settings = settings

    @staticmethod
    def get_location_relative_to_driver(ego_car_snapshot: carla.ActorSnapshot,
                                        forward: float = 0,
                                        aside: float = 0,
                                        upward: float = 0) -> carla.Location:
        offset_x = 0.32 + aside     # left
        offset_y = 0.10 + forward
        offset_z = 1.28 + upward

        ego_car_transform = ego_car_snapshot.get_transform()
        loc = ego_car_transform.location
        rot = ego_car_transform.rotation

        ego_car_velocity = ego_car_snapshot.get_velocity()
        meters_per_frame = math.sqrt(ego_car_velocity.x**2 + ego_car_velocity.y**2) / Environment.FPS       # because of the async mode, we need to compsate the path that the car travelled during the delay

        return carla.Location(
            loc.x + offset_x * math.sin(math.radians(rot.yaw)) + (offset_y + meters_per_frame) * math.cos(math.radians(rot.yaw)),
            loc.y - offset_x * math.cos(math.radians(rot.yaw)) + (offset_y + meters_per_frame) * math.sin(math.radians(rot.yaw)),
            loc.z + offset_z)

    @staticmethod
    def get_location_relative_to_point(transform: carla.Transform,
                                       forward: float = 0,
                                       aside: float = 0,
                                       upward: float = 0) -> carla.Location:
        offset_x = 0.32 + aside     # left
        offset_y = 0.10 + forward
        offset_z = 1.28 + upward

        loc = transform.location
        rot = transform.rotation

        return carla.Location(
            loc.x + offset_x * math.sin(math.radians(rot.yaw)) + offset_y * math.cos(math.radians(rot.yaw)),
            loc.y - offset_x * math.cos(math.radians(rot.yaw)) + offset_y * math.sin(math.radians(rot.yaw)),
            loc.z + offset_z)

    def load_world(self,
                   town_id: Optional[str]) -> carla.World:
        world = self.client.get_world()
        if (town_id is not None):
            desired_map_name = f'/Game/Carla/Maps/Town{town_id}'
            map_name = world.get_map().name
            if map_name != desired_map_name and map_name != (desired_map_name + '_Opt'):
                available_maps = self.client.get_available_maps()
                if desired_map_name in available_maps:
                    world = self.client.load_world(f'Town{town_id}')
                else:
                    only_basic: Callable[[str], bool] = lambda map: not map.endswith('_Opt')
                    basic_maps = [map.split('/').pop()[4:] for map in filter(only_basic, available_maps)]
                    basic_maps = ', '.join(basic_maps)
                    print(f'No map for Town{town_id}, only the following town ids are available:\n  ' +  basic_maps)
            print(f'Using the map {world.get_map().name}')

        return world

    def create_traffic(self,
                       vehicle_factory: VehicleFactory,
                       max_count: int) -> None:
        world = self.client.get_world()
        spawn_points = world.get_map().get_spawn_points()
        random.shuffle(spawn_points)
        
        vehicles = world.get_actors().filter('vehicle.*')
        if len(vehicles) >= (max_count + 1):
            return
        
        for n, transform in enumerate(spawn_points):
            if n == max_count:
                break
            other_car = vehicle_factory.make_vehicle(False, transform)
            if other_car is not None:
                vehicle_factory.configure_traffic_vehicle(other_car)
                print(f'spawned {other_car.type_id} [#{n+1}]')
                
    def add_traffic(self,
                    vehicle_factory: VehicleFactory,
                    max_count: int) -> None:
        world = self.client.get_world()
        if random.random() < 0.05:
            vehicles: list[carla.Actor] = world.get_actors().filter('vehicle.*')
            if len(vehicles) < (max_count + 1):
                other_car = vehicle_factory.make_vehicle(False)
                if other_car is not None:
                    vehicle_factory.configure_traffic_vehicle(other_car)
                    print(f'spawned {other_car.type_id} [#{len(vehicles)}]')
            
    def relocate_spectator(self,
                           spectator: carla.Actor,
                           ego_car_snapshot: carla.ActorSnapshot) -> None:
        spectator_location = Environment.get_location_relative_to_driver(ego_car_snapshot)
        
        transform = carla.Transform(spectator_location, ego_car_snapshot.get_transform().rotation)
        spectator.set_transform(transform)
