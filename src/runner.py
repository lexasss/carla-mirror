import carla

from typing import Optional, Tuple, cast

from src.user_action import ActionType, Action, CarSpawningLocation
# from src.winapi import Window

from src.mirror.base import Mirror

from src.carla.environment import CarlaEnvironment
from src.carla.vehicle_factory import VehicleFactory
from src.carla.controller import CarlaController
from src.carla.monitor import CarlaMonitor

from src.exp.logging import EventLogger

TRAFFIC_COUNT = 0
BLOCK_MIRROR_ON_CAR_APPROACHING_FROM_BEHIND = False
BLOCK_MIRROR_WHEN_CAR_BEHIND_IS_AT_DISTANCE = 10

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
        self.monitor = CarlaMonitor(self.world)
        
        self.search_target: Optional[carla.Actor] = None
        
        self.ego_car_speed = 0.0

        # self._next_search_time: float = 0
        # self._approaching_vehicle: Optional[str] = None
        # self._blocking_window: Optional[Window] = None
        
        self._last_vehicle: Optional[carla.Vehicle] = None

        self._logger = EventLogger('spawner')
        
    def make_step(self,
                  world_snapshot: carla.WorldSnapshot,
                  action: Optional[Action]) -> Tuple[carla.ActorSnapshot, Optional[carla.Actor]]:
        spawned: Optional[carla.Actor] = None

        # create traffic at random moments/locations
        # self.environment.add_traffic(self.vehicle_factory, TRAFFIC_COUNT)

        ego_car_snapshot = world_snapshot.find(self.ego_car.id)

        # spectator is sitting in the car, and we have to move it manually as there is no way to bind it to the ego-car
        self.environment.relocate_spectator(self.spectator, ego_car_snapshot)

        # respond to a keypress
        if action:
            spawned = self._execute_action(action, ego_car_snapshot)
            if spawned:
                if action.type == ActionType.SPAWN_TARGET or action.type == ActionType.SPAWN_TARGET_NEARBY:
                    self.search_target = spawned
                if action.type == ActionType.SPAWN_CAR:
                    self._last_vehicle = cast(carla.Vehicle, spawned)

        self.ego_car_speed = 3.6 * ego_car_snapshot.get_velocity().length()

        # update display
        self.controller.display_speed(ego_car_snapshot, self.ego_car_speed)
        self.controller.update_info(ego_car_snapshot)
        
        if self.search_target:
            self.controller.display_target_info(ego_car_snapshot, self.search_target)
        # if self._last_vehicle:
        #     self.controller.display_vehicle_info(ego_car_snapshot, self._last_vehicle)

        return ego_car_snapshot, spawned
    
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
            if isinstance(action.param, str):
                spawned = self.controller.spawn_prop(action.param)
        elif action.type == ActionType.SPAWN_TARGET_NEARBY:
            if isinstance(action.param, str):
                spawned = self.controller.spawn_prop_nearby(action.param, ego_car_snapshot)
        elif action.type == ActionType.SPAWN_CAR:
            if isinstance(action.param, tuple):
                location, distance = action.param
                if location == CarSpawningLocation.random:
                    spawned = self.controller.spawn_vehicle(ego_car_snapshot, self.vehicle_factory)
                else:
                    spawned = self.controller.spawn_vehicle_behind(ego_car_snapshot, self.vehicle_factory, cast(float, distance), location == CarSpawningLocation.behind_same_lane)
        if action.type == ActionType.REMOVE_TARGETS:
            self.search_target = None
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

        elif action.type == ActionType.LANE_LEFT:
            self.vehicle_factory.traffic_manager.force_lane_change(self.ego_car, False)
            print('left')
        elif action.type == ActionType.LANE_RIGHT:
            self.vehicle_factory.traffic_manager.force_lane_change(self.ego_car, True)
            print('right')

        if spawned:
            evt = str(action.type).split('.')[1].split('_')[1].lower()
            name = '_'.join(spawned.type_id.split('.')[1:])
            self._logger.log(evt, name)
                
        return spawned
