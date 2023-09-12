import carla
import math

from typing import Optional, Tuple, List, cast

from src.common.lane import Lane

class CarBehind:
    def __init__(self, vehicle: carla.Vehicle, distance: float, lane: Lane) -> None:
        self.vehicle = vehicle
        self.distance = distance
        self.lane = lane
        
class CarlaMonitor:
    def __init__(self, world: carla.World) -> None:
        self._world = world
        self._map = self._world.get_map()
        
    def get_nearest_vehicle_behind(self, ego_car_snapshot: carla.ActorSnapshot) -> Tuple[Optional[CarBehind], List[Tuple[float, Lane]]]:
        actors = self._world.get_actors().filter('vehicle.*')
        vehicles = cast(List[carla.Vehicle], actors)
        
        car_behind: Optional[CarBehind] = None
        all_distances: List[Tuple[float, Lane]] = []

        for vehicle in vehicles:
            transform = vehicle.get_transform()
            velocity = vehicle.get_velocity()
            
            is_approaching_from_behind, distance = CarlaMonitor._is_approaching_from_behind(transform, velocity, ego_car_snapshot)
            if is_approaching_from_behind:
                lane = self.get_lane(ego_car_snapshot, vehicle)
                all_distances.append((distance, lane))
                if not car_behind or distance < car_behind.distance:
                    car_behind = CarBehind(vehicle, distance, lane)

        return car_behind, all_distances
    
    def get_lane(self, ego_car_snapshot: carla.ActorSnapshot, other_car: carla.Vehicle) -> Optional[Lane]:
        
        ego_car_tranform = ego_car_snapshot.get_transform()
        ego_car_waypoint = self._map.get_waypoint(ego_car_tranform.location, True, carla.LaneType.Driving)
        
        vehicle_tranform = other_car.get_transform()
        vehicle_waypoint = self._map.get_waypoint(vehicle_tranform.location, True, carla.LaneType.Driving)
        
        if ego_car_waypoint is None or vehicle_waypoint is None:
            return None

        ego_car_lane = abs(ego_car_waypoint.lane_id)
        vehicle_lane = abs(vehicle_waypoint.lane_id)
        
        if ego_car_lane < vehicle_lane:
            return Lane.LEFT
        elif ego_car_lane > vehicle_lane:
            return Lane.RIGHT
        else:
            return Lane.SAME
    
    def get_lane_props(self, ego_car_snapshot: carla.ActorSnapshot) -> Optional[Tuple[float, float]]:
        ego_car_location = ego_car_snapshot.get_transform().location
        wp = self._map.get_waypoint(ego_car_location, True, carla.LaneType.Driving)
        if wp:
            wps = wp.next(1)
            if len(wps) > 0:
                wp_next = wps[0]
                x0 = wp.transform.location.x
                y0 = wp.transform.location.y
                dx = wp_next.transform.location.x - x0
                dy = wp_next.transform.location.y - y0
                a = dy
                b = -dx
                c = -x0 * dy + y0 * dx
                x1 = ego_car_location.x
                y1 = ego_car_location.y
                return wp.s, abs(a * x1 + b * y1 + c) / math.sqrt(a * a + b * b)
    
        return None        
    
    # Internal
    
    @staticmethod
    def _is_approaching_from_behind(transform: carla.Transform,
                                    velocity: carla.Vector3D,
                                    ego_car_snapshot: carla.ActorSnapshot,
                                    distance: Optional[float] = None) -> Tuple[bool, float]:
        ego_car_transform = ego_car_snapshot.get_transform()
        
        # other vehicle should be away at "distance" plus-minus half a meter
        l1 = transform.location
        l2 = ego_car_transform.location
        dist = math.sqrt((l1.x - l2.x)**2 + (l1.y - l2.y)**2)
        if dist < 1:    # this is ego car, ignore it
            return False, 0
        
        if distance and abs(dist - distance) > 0.5:
            return False, 0
        
        # other vehicle should move about the same direction as the ego car, plus-minus 25 degrees
        r1 = transform.rotation
        r2 = ego_car_transform.rotation
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
