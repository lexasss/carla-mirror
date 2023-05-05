import carla
import math
# import time
import sys

from typing import Optional, List, Tuple, cast

from src.user_action import ActionType, Action, CarSpawningLocation
# from src.winapi import Window

from src.mirror.base import Mirror

from src.carla.environment import CarlaEnvironment
from src.carla.vehicle_factory import VehicleFactory
from src.carla.controller import CarlaController

from src.exp.logging import Logger

TRAFFIC_COUNT = 0
BLOCK_MIRROR_ON_CAR_APPROACHING_FROM_BEHIND = False
BLOCK_MIRROR_WHEN_CAR_BEHIND_IS_AT_DISTANCE = 10

SPAWN_VEHICLE_BEHIND = 30 # meters

class Runner:
    def __init__(self,
                 environment: CarlaEnvironment,
                 vehicle_factory: VehicleFactory,
                 ego_car: carla.Vehicle,
                 mirror: Mirror) -> None:
        self.environment = environment
        self.vehicle_factory = vehicle_factory
        self.ego_car = ego_car
        self.mirror = mirror

        self.world = self.vehicle_factory.world
        self.spectator = self.world.get_spectator()
        self.controller = CarlaController(self.world)
        
        self._search_target: Optional[carla.Actor] = None
        self._last_vehicle: Optional[carla.Vehicle] = None
        # self._next_search_time: float = 0
        # self._approaching_vehicle: Optional[str] = None
        # self._blocking_window: Optional[Window] = None

        self._logger = Logger('spawner')
        
    def make_step(self,
                  world_snapshot: carla.WorldSnapshot,
                  action: Optional[Action]) -> Optional[carla.Actor]:
        spawned: Optional[carla.Actor] = None

        # create traffic at random moments/locations
        # self.environment.add_traffic(self.vehicle_factory, TRAFFIC_COUNT)

        ego_car_snapshot = world_snapshot.find(self.ego_car.id)

        # spectator is sitting in the car, and we have to move it manually as there is no way to bind it to the ego-car
        self.environment.relocate_spectator(self.spectator, ego_car_snapshot)

        # respond to a keypress
        if action is not None:
            spawned = self._execute_action(action, ego_car_snapshot)
            if spawned is not None:
                if action.type == ActionType.SPAWN_TARGET or action.type == ActionType.SPAWN_TARGET_NEARBY:
                    self._search_target = spawned
                if action.type == ActionType.SPAWN_CAR:
                    self._last_vehicle = cast(carla.Vehicle, spawned)

        # update display
        self.controller.display_speed(ego_car_snapshot)
        self.controller.update_info(ego_car_snapshot)
        
        if self._search_target is not None:
            self.controller.display_target_info(ego_car_snapshot, self._search_target)
        if self._last_vehicle is not None:
            self.controller.display_vehicle_info(ego_car_snapshot, self._last_vehicle)

        return spawned
    
    def get_nearest_vehicle_behind(self, ego_car_snapshot: carla.ActorSnapshot) -> Tuple[Optional[carla.Vehicle], float]:
        actors = self.world.get_actors().filter('vehicle.*')
        vehicles = cast(List[carla.Vehicle], actors)
        
        min_distance = sys.float_info.max
        result: Optional[carla.Vehicle] = None

        for vehicle in vehicles:
            transform = vehicle.get_transform()
            velocity = vehicle.get_velocity()
            
            is_approaching_from_behind, distance = self._is_approaching_from_behind(transform, velocity, ego_car_snapshot)
            if is_approaching_from_behind and distance < min_distance:
                min_distance = distance
                result = vehicle
                
        return result, min_distance
    
    def get_distance_to_search_target(self, ego_car_snapshot: carla.ActorSnapshot) -> float:
        if self._search_target is None:
            return 0
        
        return self.controller.get_distance_to(ego_car_snapshot, self._search_target)

    # def check_traffic_event(self, ego_car_snapshot: carla.ActorSnapshot) -> None:
    #     if time.time() > self._next_search_time:
    #         actors = self.world.get_actors().filter('vehicle.*')
    #         vehicles = cast(List[carla.Vehicle], actors)

    #         if self._blocking_window is not None:
    #             self._blocking_window.close()
    #             self._blocking_window = None
    #         if not self.mirror.enabled:
    #             self.mirror.enabled = True
                
    #         for vehicle in vehicles:
    #             transform = vehicle.get_transform()
    #             velocity = vehicle.get_velocity()
                
    #             if self._is_approaching_from_behind(
    #                 transform, 
    #                 velocity, 
    #                 ego_car_snapshot,
    #                 BLOCK_MIRROR_WHEN_CAR_BEHIND_IS_AT_DISTANCE
    #             ):
    #                 self._approaching_vehicle = vehicle.type_id
    #                 self._next_search_time = time.time() + 3
    #                 print(f'RUN: {vehicle.type_id} {vehicle.get_transform().location} is approaching the ego car {ego_car_snapshot.get_transform().location}')
    #                 #self._blocking_window = Window()
    #                 self.mirror.enabled = not BLOCK_MIRROR_ON_CAR_APPROACHING_FROM_BEHIND
    #                 break
    #     else:
    #         self.carla_controller.display_info(ego_car_snapshot, f'{self._approaching_vehicle} is approaching the ego car')
    
    # Internal
        
    def _execute_action(self,
                        action: Action,
                        ego_car_snapshot: carla.ActorSnapshot) -> Optional[carla.Actor]:
        spawned: Optional[carla.Actor] = None
        
        if action.type == ActionType.SPAWN_TARGET:
            if action.param is not None:
                spawned = self.controller.spawn_prop(action.param)
        elif action.type == ActionType.SPAWN_TARGET_NEARBY:
            if action.param is not None:
                spawned = self.controller.spawn_prop_nearby(action.param, ego_car_snapshot)
        elif action.type == ActionType.SPAWN_CAR:
            if action.param == CarSpawningLocation.random:
                spawned = self.controller.spawn_vehicle(ego_car_snapshot, self.vehicle_factory)
            elif action.param == CarSpawningLocation.behind_next_lane:
                spawned = self.controller.spawn_vehicle_behind(ego_car_snapshot, self.vehicle_factory, SPAWN_VEHICLE_BEHIND)
            elif action.param == CarSpawningLocation.behind_same_lane:
                spawned = self.controller.spawn_vehicle_behind(ego_car_snapshot, self.vehicle_factory, SPAWN_VEHICLE_BEHIND, True)
        if action.type == ActionType.REMOVE_TARGETS:
            self._search_target = None
        if action.type == ActionType.REMOVE_CARS:
            self._last_vehicle = None

        elif action.type == ActionType.PRINT_INFO:
            self.controller.print_closest_waypoint(ego_car_snapshot)
        elif action.type == ActionType.TOGGLE_NIGHT:
            self.controller.toiggle_night()
        elif action.type == ActionType.TOGGLE_MIRROR_DIMMING:
            self.mirror.toggle_brightness()

        elif action.type == ActionType.START_SCENARIO:
            self.controller.display_info(ego_car_snapshot, 'OPENED')
        elif action.type == ActionType.STOP_SCENARIO:
            self.controller.display_info(ego_car_snapshot, 'DONE')
        elif action.type == ActionType.FREEZE:
            self.controller.display_info(ego_car_snapshot, 'CLOSED')
        elif action.type == ActionType.UNFREEZE:
            self.controller.display_info(ego_car_snapshot, 'OPENED')

        if spawned is not None:    
            self._logger.log(action.type, spawned.type_id)
                
        return spawned
    
    def _is_approaching_from_behind(self,
                                   transform: carla.Transform,
                                   velocity: carla.Vector3D,
                                   ego_car_snapshot: carla.ActorSnapshot,
                                   distance: Optional[float] = None) -> Tuple[bool, float]:
        # other vehicle should be away at "distance" plus-minus half a meter
        l1 = transform.location
        l2 = ego_car_snapshot.get_transform().location
        dist = math.sqrt((l1.x - l2.x)**2 + (l1.y - l2.y)**2)
        if dist < 1:    # this is ego car, ignore it
            return False, 0
        
        if distance is not None and abs(dist - distance) > 0.5:
            return False, 0
        
        # other vehicle should move about the same direction as the ego car, plus-minus 15 degrees
        r1 = transform.rotation
        r2 = ego_car_snapshot.get_transform().rotation
        if abs(r1.yaw - r2.yaw) > 25:
            # if dist < 30:
            #     print(f'DIRECTION is not same: {abs(r1.yaw - r2.yaw):.2f}')
            return False, 0

        # lets move 1 meter forward: the distance to the ego car should decrease if the object is behind
        x = l1.x + 1 * math.cos(math.radians(r1.yaw))
        y = l1.y + 1 * math.sin(math.radians(r1.yaw))
        dist2 = math.sqrt((x - l2.x)**2 + (y - l2.y)**2)
        if dist < 10:   # other vehicle is definitely on the same road
            if dist2 > dist:
                return False, 0
        elif (dist - dist2) < 0.7:   # other vehicle is moving in the same direction, but certainly on some other (parallel) road
            # if dist < 30:
            #     print(f'VEHICLE is not behind: {(dist - dist2):.2f}')
            return False, 0

        # other vehicle should move faster than the ego car
        v2 = ego_car_snapshot.get_velocity()
        s1 = math.sqrt(velocity.x**2 + velocity.y**2)
        s2 = math.sqrt(v2.x**2 + v2.y**2)
        if s1 < s2:
            # if dist < 30:
            #     print(f'SPPED is slower thatn the ego car: {s1:.2f} < {s2:.2f}')
            return False, 0
        
        return True, dist