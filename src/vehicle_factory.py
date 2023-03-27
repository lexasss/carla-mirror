import random
import time
import carla

from typing import Optional, Tuple, cast

class VehicleFactory:
    #EGO_CAR_TYPE = 'vehicle.lincoln.mkz_2017'
    EGO_CAR_TYPE = 'vehicle.toyota.prius'
    #EGO_CAR_TYPE = 'vehicle.audi.tt'
    #EGO_CAR_TYPE = 'vehicle.mercedes.coupe_2020'
    
    def __init__(self, client: carla.Client) -> None:
        self.world = client.get_world()
        self.traffic_manager = client.get_trafficmanager()
        
    def get_ego_car(self) -> Tuple[carla.Vehicle, bool]:
        time.sleep(1)   # small pause, othewise the world.get_actors() list is empty
        
        vehicles = self.world.get_actors().filter(VehicleFactory.EGO_CAR_TYPE)
        
        if (len(vehicles) == 0):
            print(f'No vehicles found, spawining a new one')
            vehicle: Optional[carla.Vehicle] = None
            while vehicle is None:
                vehicle = self.make_vehicle(True)
                time.sleep(0.5)
            return (vehicle, True)
        else:
            print(f'Found a vehicle, attaching the mirror')
            vehicle = cast(carla.Vehicle, vehicles[0])
            return (vehicle, False)

    def make_vehicle(self,
                     is_ego_car: bool,
                     transform: Optional[carla.Transform] = None) -> Optional[carla.Vehicle]:
        vehicle_bp: Optional[carla.ActorBlueprint] = None
        if is_ego_car:
            vehicle_bp = self.world.get_blueprint_library().filter(VehicleFactory.EGO_CAR_TYPE)[0]
            vehicle_bp.set_attribute('role_name', 'hero')
        else:
            vehicles_bps = self.world.get_blueprint_library().filter('vehicle.*')
            vehicles_bps = [x for x in vehicles_bps if int(x.get_attribute('number_of_wheels')) == 4]
            vehicle_bp = random.choice(vehicles_bps)
            
            while vehicle_bp.id == VehicleFactory.EGO_CAR_TYPE:
                vehicle_bp = random.choice(vehicles_bps)
        
        if transform is None:
            spawn_points = self.world.get_map().get_spawn_points()
            if is_ego_car:
                transform = spawn_points[0]       # ego-car appears always in the same location
            else:
                transform = random.choice(spawn_points)
            
        if vehicle_bp.has_attribute('color'):
            color = random.choice(vehicle_bp.get_attribute('color').recommended_values)
            vehicle_bp.set_attribute('color', color)
        if vehicle_bp.has_attribute('driver_id'):
            driver_id = random.choice(vehicle_bp.get_attribute('driver_id').recommended_values)
            vehicle_bp.set_attribute('driver_id', driver_id)

        try:
            vehicle = cast(carla.Vehicle, self.world.spawn_actor(vehicle_bp, transform))
            vehicle.set_autopilot(True)
        except:
            return None
        
        return vehicle

    def configure_traffic_vehicle(self,
                                  vehicle: carla.Vehicle) -> None:
        self.traffic_manager.vehicle_percentage_speed_difference(vehicle, -20)
        self.traffic_manager.ignore_lights_percentage(vehicle, 100)
        self.traffic_manager.ignore_signs_percentage(vehicle, 100)
        #self.traffic_manager.random_left_lanechange_percentage(vehicle, 20)
        #self.traffic_manager.random_right_lanechange_percentage(vehicle, 20)
   
    