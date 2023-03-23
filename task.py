import math
import random
import carla

from typing import Optional, Callable
from environment import Environment
from vehicle_factory import VehicleFactory

class Task:
    def __init__(self, world: carla.World) -> None:
        self.world = world
        self.debug = world.debug
        
    def create_target(self, name: str, transform: carla.Transform) -> Optional[carla.Actor]:
        bp = self.world.get_blueprint_library().find(f'static.prop.{name}')
        return self.world.spawn_actor(bp, transform) if bp is not None else None
    
    def display_target_info(self, ego_car_snapshot: carla.ActorSnapshot, target: carla.Actor) -> None:
        transform = ego_car_snapshot.get_transform()
        
        loc = transform.location
        dist = loc.distance(target.get_location())
        
        location = Environment.get_location_relative_to_driver(ego_car_snapshot, 0.9, 0.07, -0.28)

        name = target.type_id.split('.')[2]
        self.debug.draw_string(location, f'Distance to the {name}: {dist:.2f} m', color = carla.Color(0, 255, 255))

    def display_speed(self, ego_car_snapshot: carla.ActorSnapshot) -> None:
        vector = ego_car_snapshot.get_velocity()
        speed = 3.6 * math.sqrt(vector.x**2 + vector.y**2 + vector.z**2)
        display_location = Environment.get_location_relative_to_driver(ego_car_snapshot, 0.9, 0.07, -0.30)
        self.debug.draw_string(display_location, f'{speed:.2f} km/h', color = carla.Color(255, 255, 0))

    def display_info(self, ego_car_snapshot: carla.ActorSnapshot, text: str) -> None:
        display_location = Environment.get_location_relative_to_driver(ego_car_snapshot, 0.9, 0.07, -0.32)
        self.debug.draw_string(display_location, text, color = carla.Color(255, 128, 128), life_time = -1)

    def display_direction_to(self, ego_car_snapshot: carla.ActorSnapshot, actor: carla.Actor) -> None:
        ego_car_location = Environment.get_location_relative_to_driver(ego_car_snapshot, forward = 3, aside = 0.05, upward = -0.26)
        
        # draw_arrow and draw_line are buggy, they do not remove the arrow/line after "life_time" period
        self.debug.draw_arrow(ego_car_location, actor.get_location(), 0.005, color = carla.Color(0, 255, 255), life_time = -1)

    def spawn_vehicle(self,
                      ego_car_snapshot: carla.ActorSnapshot,
                      vehicle_factory: VehicleFactory) -> Optional[carla.Actor]:
        ego_car_tranform = ego_car_snapshot.get_transform()
        ego_car_waypoint = self.world.get_map().get_waypoint(ego_car_tranform.location, True, carla.LaneType.Driving)
        if ego_car_waypoint is None:
            return None

        spawn_points = self.world.get_map().get_spawn_points()
        random.shuffle(spawn_points)
        
        vehicle: Optional[carla.Actor] = None
        while vehicle is None:
            vehicle_transform = random.choice(spawn_points)
            vehicle_waypoint = self.world.get_map().get_waypoint(vehicle_transform.location, True, carla.LaneType.Driving)
            if vehicle_waypoint is None or abs(ego_car_waypoint.lane_id) == abs(vehicle_waypoint.lane_id):
                continue
            
            vehicle = vehicle_factory.make_vehicle(False, vehicle_transform)
            
        return vehicle
        
    def spawn_vehicle_behind(self,
                             ego_car_snapshot: carla.ActorSnapshot,
                             vehicle_factory: VehicleFactory,
                             distance: float) -> Optional[carla.Actor]:
        ego_car_tranform = ego_car_snapshot.get_transform()
        ego_car_waypoint = self.world.get_map().get_waypoint(ego_car_tranform.location, True, carla.LaneType.Driving)
        
        vehicle_location = Environment.get_location_relative_to_driver(ego_car_snapshot, -distance)
        vehicle_waypoint = self.world.get_map().get_waypoint(vehicle_location, True, carla.LaneType.Driving)

        if ego_car_waypoint is None or vehicle_waypoint is None:
            return None
        
        if abs(ego_car_waypoint.lane_id) != abs(vehicle_waypoint.lane_id):
            return None

        side_offset = 0
        if vehicle_waypoint.lane_change == ego_car_waypoint.lane_change:
            if carla.LaneChange.Left == ego_car_waypoint.lane_change or carla.LaneChange.Both == ego_car_waypoint.lane_change:
                side_offset = ego_car_waypoint.lane_width
            elif carla.LaneChange.Right == ego_car_waypoint.lane_change:
                side_offset = -ego_car_waypoint.lane_width
        
        vehicle_location = Environment.get_location_relative_to_point(vehicle_waypoint.transform, aside = side_offset)
        new_vehicle_waypoint = self.world.get_map().get_waypoint(vehicle_location, True, carla.LaneType.Driving)

        # debug
        if new_vehicle_waypoint is None:
            return None
            
        printInfo: Callable[[str, carla.Waypoint], None] = lambda name, wp : print(f"""{name} lane: id = {wp.lane_id}, type = {wp.lane_type}, change = {wp.lane_change}, loc =\t{wp.transform.location.x:.2f}\t{wp.transform.location.y:.2f}""")
        printInfo('EC', ego_car_waypoint)
        printInfo('VO', vehicle_waypoint)
        printInfo('VN', new_vehicle_waypoint)
        
        vehicle_transform = carla.Transform(vehicle_location, new_vehicle_waypoint.transform.rotation)
        vehicle = vehicle_factory.make_vehicle(False, vehicle_transform)
        
        if vehicle is not None:
            vehicle_factory.configure_traffic_vehicle(vehicle)

        return vehicle
    
    def spawn_prop(self, name: str) -> Optional[carla.Actor]:
        transform = carla.Transform(
            self.world.get_random_location_from_navigation(),
            carla.Rotation())
        return self.create_target(name, transform)
    
    def spawn_prop_nearby(self, name: str, ego_car_snapshot: carla.ActorSnapshot) -> Optional[carla.Actor]:
        waypoint = self.world.get_map().get_waypoint(
            ego_car_snapshot.get_transform().location,
            project_to_road = True,
            lane_type = carla.LaneType.Sidewalk)
        if waypoint is not None:
            return self.create_target(name, waypoint.transform)
        else:
            return None
    
    def toiggle_night(self):
        weather = self.world.get_weather()
        weather.sun_altitude_angle = -90 if weather.sun_altitude_angle > 0 else 90
        self.world.set_weather(weather)
    
    def print_spawn_points(self) -> None:
        for p in self.world.get_map().get_spawn_points():
            print(f'{p.location.x} {p.location.y}')
    def print_landmarks(self) -> None:
        for p in self.world.get_map().get_all_landmarks():
            loc = p.transform.location
            print(f'{loc.x} {loc.y}')
    def print_lights(self) -> None:
        for p in self.world.get_lightmanager().get_all_lights():
            print(f'{p.location.x} {p.location.y}')
    def print_waypoints(self) -> None:
        for p in self.world.get_map().get_topology():
            loc = p[0].transform.location
            print(f'{loc.x} {loc.y}')
    def print_waypoints_gen(self) -> None:
        waypoints = self.world.get_map().generate_waypoints(5)
        output = open('wp.txt', 'w')
        for p in waypoints:
            output.write(f'{p.transform.location.x} {p.transform.location.y}\n')
    def print_closest_waypoint(self, ego_car_snapshot: carla.ActorSnapshot) -> None:
        waypoint = self.world.get_map().get_waypoint(
            ego_car_snapshot.get_transform().location,
            project_to_road=True,
            lane_type=carla.LaneType.Driving | carla.LaneType.Shoulder)
        if waypoint is not None:
            print("Waypoint: " + str(waypoint.transform.location))
            print(f"Current lane type: {waypoint.lane_type}, {waypoint.lane_id}, {waypoint.lane_change}, {waypoint.lane_width}")
