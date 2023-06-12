import random
import carla

from typing import Optional

from src.carla.environment import CarlaEnvironment
from src.carla.vehicle_factory import VehicleFactory

DISPLAY_X = 0.9
DISPLAY_Y = 0.07
DISPLAY_Z = -0.25
DISPLAY_LINE_HEIGHT = 0.025

DISPLAY_ACTOR_INFO_COLOR = carla.Color(0, 255, 255)
DISPLAY_EGOCAR_INFO_COLOR = carla.Color(255, 255, 0)
DISPLAY_EXP_INFO_COLOR = carla.Color(255, 128, 128)

class CarlaController:
    def __init__(self, world: carla.World) -> None:
        self.world = world
        self.debug = world.debug

        self._map = self.world.get_map()        
        self._info: Optional[str] = None
    
    # Info display
    
    def display_target_info(self, ego_car_snapshot: carla.ActorSnapshot, target: carla.Actor) -> None:
        display_location = CarlaEnvironment.get_location_relative_to_driver(ego_car_snapshot, DISPLAY_X, DISPLAY_Y, DISPLAY_Z - 0 * DISPLAY_LINE_HEIGHT)

        name = target.type_id.split('.')[2]
        dist = CarlaController.get_distance_to(ego_car_snapshot, target)
        self.debug.draw_string(display_location, f'Target: {name.upper()}, {dist:.2f} m', color = DISPLAY_ACTOR_INFO_COLOR)
        # self.debug.draw_string(display_location, f'Target: {name.upper()}', color = DISPLAY_ACTOR_INFO_COLOR)

    def display_vehicle_info(self, ego_car_snapshot: carla.ActorSnapshot, vehicle: carla.Vehicle) -> None:
        display_location = CarlaEnvironment.get_location_relative_to_driver(ego_car_snapshot, DISPLAY_X, DISPLAY_Y, DISPLAY_Z - 1 * DISPLAY_LINE_HEIGHT)

        name = vehicle.type_id.split('.')[2]
        velocity = 3.6 * vehicle.get_velocity().length()
        dist = CarlaController.get_distance_to(ego_car_snapshot, vehicle)
        self.debug.draw_string(display_location, f'{name} at {dist:.1f} m, moving {velocity:.1f} km/h', color = DISPLAY_ACTOR_INFO_COLOR)

    def display_speed(self, ego_car_snapshot: carla.ActorSnapshot, speed: float) -> None:
        display_location = CarlaEnvironment.get_location_relative_to_driver(ego_car_snapshot, DISPLAY_X, DISPLAY_Y, DISPLAY_Z - 2 * DISPLAY_LINE_HEIGHT)
        self.debug.draw_string(display_location, f'{speed:.1f} km/h', color = DISPLAY_EGOCAR_INFO_COLOR)

    def display_info(self, ego_car_snapshot: carla.ActorSnapshot, text: Optional[str] = None) -> None:
        self._info = text
        self.update_info(ego_car_snapshot)

    def update_info(self, ego_car_snapshot: carla.ActorSnapshot):
        if self._info:
            display_location = CarlaEnvironment.get_location_relative_to_driver(ego_car_snapshot, DISPLAY_X, DISPLAY_Y, DISPLAY_Z - 3 * DISPLAY_LINE_HEIGHT)
            self.debug.draw_string(display_location, self._info, color = DISPLAY_EXP_INFO_COLOR, life_time = -1)

    # Other visible cues
    
    def display_direction_to(self, ego_car_snapshot: carla.ActorSnapshot, actor: carla.Actor) -> None:
        ego_car_location = CarlaEnvironment.get_location_relative_to_driver(ego_car_snapshot, 3, 0.05, -0.26)
        
        # draw_arrow and draw_line are buggy, they do not remove the arrow/line after "life_time" period
        self.debug.draw_arrow(ego_car_location, actor.get_location(), 0.005, color = carla.Color(0, 255, 255), life_time = -1)

    # Spawning
    
    def spawn_vehicle(self,
                      ego_car_snapshot: carla.ActorSnapshot,
                      vehicle_factory: VehicleFactory) -> Optional[carla.Actor]:
        ego_car_tranform = ego_car_snapshot.get_transform()
        ego_car_waypoint = self._map.get_waypoint(ego_car_tranform.location, True, carla.LaneType.Driving)
        if ego_car_waypoint is None:
            return None

        spawn_points = self._map.get_spawn_points()
        random.shuffle(spawn_points)
        
        vehicle: Optional[carla.Actor] = None
        while vehicle is None:
            vehicle_transform = random.choice(spawn_points)
            vehicle_waypoint = self._map.get_waypoint(vehicle_transform.location, True, carla.LaneType.Driving)
            if vehicle_waypoint is None or abs(ego_car_waypoint.lane_id) == abs(vehicle_waypoint.lane_id):
                continue
            
            vehicle = vehicle_factory.make_vehicle(False, vehicle_transform)
            
        vehicle_factory.configure_traffic_vehicle(vehicle)
            
        return vehicle
        
    def spawn_vehicle_behind(self,
                             ego_car_snapshot: carla.ActorSnapshot,
                             vehicle_factory: VehicleFactory,
                             distance: float,
                             same_lane: bool = False) -> Optional[carla.Actor]:
        ego_car_tranform = ego_car_snapshot.get_transform()
        ego_car_waypoint = self._map.get_waypoint(ego_car_tranform.location, True, carla.LaneType.Driving)
        
        vehicle_location = CarlaEnvironment.get_location_relative_to_driver(ego_car_snapshot, -distance)
        vehicle_waypoint = self._map.get_waypoint(vehicle_location, True, carla.LaneType.Driving)

        if ego_car_waypoint is None or vehicle_waypoint is None:
            print('CCR: No waypoint to spawn the car')
            return None
        
        if abs(ego_car_waypoint.lane_id) != abs(vehicle_waypoint.lane_id):
            print(f'CCR: Lanes are different: {ego_car_waypoint.lane_id} != {vehicle_waypoint.lane_id}')
            return None

        side_offset = 0
        if not same_lane and vehicle_waypoint.lane_change == ego_car_waypoint.lane_change:
            if carla.LaneChange.Left == ego_car_waypoint.lane_change or carla.LaneChange.Both == ego_car_waypoint.lane_change:
                side_offset = ego_car_waypoint.lane_width
            elif carla.LaneChange.Right == ego_car_waypoint.lane_change:
                side_offset = -ego_car_waypoint.lane_width
        
        vehicle_location = CarlaEnvironment.get_location_relative_to_point(vehicle_waypoint.transform, left = side_offset)
        vehicle_location.z += 0.2
        new_vehicle_waypoint = self._map.get_waypoint(vehicle_location, True, carla.LaneType.Driving)

        if new_vehicle_waypoint is None:
            print('CCR: No new waypoint')
            return None
            
        # debug
        # printInfo: Callable[[str, carla.Waypoint], None] = lambda name, wp : print(f"""{name} lane: id = {wp.lane_id}, type = {wp.lane_type}, change = {wp.lane_change}, loc =\t{wp.transform.location.x:.2f}\t{wp.transform.location.y:.2f}""")
        # printInfo('EC', ego_car_waypoint)
        # printInfo('VO', vehicle_waypoint)
        # printInfo('VN', new_vehicle_waypoint)
        
        vehicle_transform = carla.Transform(vehicle_location, new_vehicle_waypoint.transform.rotation)
        vehicle = vehicle_factory.make_vehicle(False, vehicle_transform)
        
        if vehicle:
            vehicle_factory.configure_traffic_vehicle(vehicle)
            
        return vehicle
    
    def spawn_prop(self, name: str) -> Optional[carla.Actor]:
        result: Optional[carla.Actor] = None
        
        max_attempts = 10
        while result is None and max_attempts > 0:
            try:
                location = self.world.get_random_location_from_navigation()
                waypoint = self._map.get_waypoint(
                    location,
                    project_to_road = True,
                    lane_type = carla.LaneType.Sidewalk)
                if waypoint:
                    result = self._create_target(name, waypoint.transform)
                # transform = carla.Transform(
                #     self.world.get_random_location_from_navigation(),
                #     carla.Rotation())
                # result = _self.create_target(name, transform)
            except:
                pass
            finally:
                max_attempts -= 1
            
        return result
    
    def spawn_prop_nearby(self, name: str, ego_car_snapshot: carla.ActorSnapshot) -> Optional[carla.Actor]:
        waypoint = self._map.get_waypoint(
            ego_car_snapshot.get_transform().location,
            project_to_road = True,
            lane_type = carla.LaneType.Sidewalk)
        if waypoint:
            return self._create_target(name, waypoint.transform)
        else:
            return None
    
    # Chnage the environment
    
    def toiggle_night(self):
        weather = self.world.get_weather()
        weather.sun_altitude_angle = -90 if weather.sun_altitude_angle > 0 else 90
        self.world.set_weather(weather)
    
    # Debug info print to console
    
    def print_spawn_points(self) -> None:
        output = open('logs/spawns.txt', 'w')
        output.writelines([f'{p.location.x}\t{p.location.y}\n' for p in self._map.get_spawn_points()])
    def print_landmarks(self) -> None:
        output = open('logs/landmarks.txt', 'w')
        output.writelines([f'{p.transform.location.x}\t{p.transform.location.y}\n' for p in self._map.get_all_landmarks()])
    def print_lights(self) -> None:
        output = open('logs/lights.txt', 'w')
        output.writelines([f'{p.location.x}\t{p.location.y}\n' for p in self.world.get_lightmanager().get_all_lights()])
    def print_map_topology(self) -> None:
        output = open('logs/topology.txt', 'w')
        output.writelines([f'{p[0].transform.location.x}\t{p[0].transform.location.y}\n' for p in self._map.get_topology()])
    def print_waypoints(self) -> None:
        output = open('logs/waypoints.txt', 'w')
        output.writelines([f'{p.transform.location.x}\t{p.transform.location.y}\n' for p in self._map.generate_waypoints(5)])
    def print_closest_waypoint(self, object: Optional[carla.ActorSnapshot]) -> None:
        if object:
            output = open('logs/custom.txt', 'a')
            waypoint = self._map.get_waypoint(
                object.get_transform().location,
                project_to_road=True,
                lane_type=carla.LaneType.Driving | carla.LaneType.Shoulder)
            if waypoint:
                output.write(f'{waypoint.transform.location.x}\t{waypoint.transform.location.y}\t{waypoint.transform.location.x}\t{waypoint.transform.location.y}\t{waypoint.lane_type}\t{waypoint.lane_id}\t{waypoint.lane_change}\t{waypoint.lane_width}\n')

    @staticmethod
    def get_distance_to(ego_car_snapshot: carla.ActorSnapshot, target: carla.Actor) -> float:
        transform = ego_car_snapshot.get_transform()
        
        loc = transform.location
        return loc.distance(target.get_location())
        
    # Internal
    
    def _create_target(self, name: str, transform: carla.Transform) -> Optional[carla.Actor]:
        bp = self.world.get_blueprint_library().find(f'static.prop.{name}')
        return self.world.spawn_actor(bp, transform) if bp is not None else None
    