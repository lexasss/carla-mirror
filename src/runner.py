import carla
import math
import time

from typing import Optional, List, cast

from src.environment import Environment
from src.vehicle_factory import VehicleFactory
from src.controller import ActionType, Action
from src.task import Task
from src.winapi import Window
from src.mirror.base import Mirror

TRAFFIC_COUNT = 0

class Runner:
    def __init__(self,
                 environment: Environment,
                 vehicle_factory: VehicleFactory,
                 ego_car: carla.Vehicle,
                 mirror: Mirror) -> None:
        self.environment = environment
        self.vehicle_factory = vehicle_factory
        self.ego_car = ego_car
        self.mirror = mirror

        self.world = self.vehicle_factory.world
        self.spectator = self.world.get_spectator()
        self.task = Task(self.world)
        
        self._search_target: Optional[carla.Actor] = None
        self._next_search_time: float = 0
        self._approaching_vehicle: Optional[str] = None
        self._blocking_window: Optional[Window] = None

    def make_step(self,
                  world_snapshot: carla.WorldSnapshot,
                  action: Optional[Action]) -> Optional[carla.Actor]:
        # create traffic at random moments/locations
        self.environment.add_traffic(self.vehicle_factory, TRAFFIC_COUNT)
            
        ego_car_snapshot = world_snapshot.find(self.ego_car.id)

        # spectator is sitting in the car, and we have to move it manually as there is no way to bind it to the ego-car
        self.environment.relocate_spectator(self.spectator, ego_car_snapshot)

        # update display
        self.task.display_speed(ego_car_snapshot)
        if self._search_target is not None:
            self.task.display_target_info(ego_car_snapshot, self._search_target)
            # self.task.show_direction_to(ego_car_snapshot, search_target)

        vehicles = self.world.get_actors().filter('vehicle.*')
        self._check_traffic_event(cast(List[carla.Vehicle], vehicles), ego_car_snapshot)
        
        # respond to a keypress
        spawned: Optional[carla.Actor] = None
        if action is not None:
            spawned = self._execute_action(action, ego_car_snapshot)
            if spawned is not None:
                self._search_target = spawned
                
        return spawned
        
    # Internal
    
    def _execute_action(self,
                       action: Action,
                       ego_car_snapshot: carla.ActorSnapshot) -> Optional[carla.Actor]:
        spawned: Optional[carla.Actor] = None
        
        if action.type == ActionType.SPAWN_TARGET:
            if action.param is not None:
                spawned = self.task.spawn_prop(action.param)
                print('Target created')
        if action.type == ActionType.SPAWN_TARGET_NEARBY:
            if action.param is not None:
                spawned = self.task.spawn_prop_nearby(action.param, ego_car_snapshot)
                print('Target created')
        elif action.type == ActionType.SPAWN_CAR:
            if action.param == 'random':
                spawned = self.task.spawn_vehicle(ego_car_snapshot, self.vehicle_factory)
            elif action.param == 'behind':
                spawned = self.task.spawn_vehicle_behind(ego_car_snapshot, self.vehicle_factory, 30)
        elif action.type == ActionType.PRINT_INFO:
            self.task.print_closest_waypoint(ego_car_snapshot)
        elif action.type == ActionType.TOGGLE_NIGHT:
            self.task.toiggle_night()
        elif action.type == ActionType.TOGGLE_MIRROR_DIMMING:
            self.mirror.toggle_brightness()
    
        return spawned
    
    def _check_traffic_event(self,
                            vehicles: List[carla.Vehicle],
                            ego_car_snapshot: carla.ActorSnapshot) -> None:
        if time.time() > self._next_search_time:
            if self._blocking_window is not None:
                self._blocking_window.close()
                self._blocking_window = None
            if not self.mirror.enabled:
                self.mirror.enabled = True
                
            for vehicle in vehicles:
                transform = vehicle.get_transform()
                if self._is_approaching_from_behind(transform, vehicle.get_velocity(), ego_car_snapshot, 10):
                    self._approaching_vehicle = vehicle.type_id
                    self._next_search_time = time.time() + 3
                    print(f'{vehicle.type_id} {vehicle.get_transform().location} is approaching the ego car {ego_car_snapshot.get_transform().location}')
                    #self._blocking_window = Window()
                    self.mirror.enabled = False
                    break
        else:
            self.task.display_info(ego_car_snapshot, f'{self._approaching_vehicle} is approaching the ego car')
    
    def _is_approaching_from_behind(self,
                                   transform: carla.Transform,
                                   velocity: carla.Vector3D,
                                   ego_car_snapshot: carla.ActorSnapshot,
                                   distance: float) -> bool:
        # other vehicle should be awayt at "distance" plus-minus half a meter
        l1 = transform.location
        l2 = ego_car_snapshot.get_transform().location
        dist = math.sqrt((l1.x - l2.x)**2 + (l1.y - l2.y)**2)
        if dist < 1:    # this is ego car, ignore it
            return False
        
        if abs(dist - distance) > 0.5:
            return False
        
        # other vehicle should move about the same direction as the ego car, plus-minus 15 degrees
        r1 = transform.rotation
        r2 = ego_car_snapshot.get_transform().rotation
        if abs(r1.yaw - r2.yaw) > 15:
            return False

        # lets move 1 meter forward: the distance to the ego car should decrease if the object is behind
        x = l1.x + 1 * math.cos(math.radians(r1.yaw))
        y = l1.y + 1 * math.sin(math.radians(r1.yaw))
        dist2 = math.sqrt((x - l2.x)**2 + (y - l2.y)**2)
        if dist2 > dist:
            return False

        # other vehicle should move faster than the ego car
        v2 = ego_car_snapshot.get_velocity()
        s1 = math.sqrt(velocity.x**2 + velocity.y**2)
        s2 = math.sqrt(v2.x**2 + v2.y**2)
        if s1 < s2:
            print(f'speed : car = {s1:.2f} m/s, ego = {s2:.2f} m/s')
            return False
        
        return True