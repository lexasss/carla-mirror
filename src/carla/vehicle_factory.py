import random
import time
import carla

from typing import Optional, Tuple, cast

PASSENGE_CARS = [
    'vehicle.audi.a2',
    'vehicle.audi.etron',
    'vehicle.audi.tt',
    'vehicle.bmw.grandtourer',
    'vehicle.chevrolet.impala',
    'vehicle.citroen.c3',
    'vehicle.dodge.charger_2020',
    'vehicle.dodge.charger_police',
    'vehicle.dodge.charger_police_2020',
    'vehicle.ford.crown',
    'vehicle.ford.mustang',
    'vehicle.jeep.wrangler_rubicon',
    'vehicle.lincoln.mkz_2017',
    'vehicle.lincoln.mkz_2020',
    'vehicle.mercedes.coupe',
    'vehicle.mercedes.coupe_2020',
    'vehicle.micro.microlino',
    'vehicle.mini.cooper_s',
    'vehicle.mini.cooper_s_2021',
    'vehicle.nissan.micra',
    'vehicle.nissan.patrol',
    'vehicle.nissan.patrol_2021',
    'vehicle.seat.leon',
    'vehicle.tesla.model3',
    'vehicle.toyota.prius',
    'vehicle.tesla.cybertruck',
]

MANUAL_EGO_CAR_TYPE = 'vehicle.dreyevr.egovehicle'
AUTO_EGO_CAR_TYPE = 'vehicle.lincoln.mkz_2017'
# EGO_CAR_TYPE = 'vehicle.toyota.prius'
# EGO_CAR_TYPE = 'vehicle.audi.tt'
# EGO_CAR_TYPE = 'vehicle.mercedes.coupe_2020'

class VehicleFactory:
    
    ego_car_type: str
    
    def __init__(self, client: carla.Client) -> None:
        self.world = client.get_world()
        
        try:
            self.traffic_manager = client.get_trafficmanager()
        except:
            self.traffic_manager = None
            print(f'CVF: Traffic manager is not available')
        
    @staticmethod
    def set_driving_mode(is_manual_mode: bool):
        if is_manual_mode:
            VehicleFactory.ego_car_type = MANUAL_EGO_CAR_TYPE
        else:
            VehicleFactory.ego_car_type = AUTO_EGO_CAR_TYPE
            
    def get_ego_car(self) -> Tuple[carla.Vehicle, bool]:
        time.sleep(1)   # small pause, othewise the world.get_actors() list is empty
        
        vehicles = self.world.get_actors().filter(VehicleFactory.ego_car_type)
        
        if (len(vehicles) == 0):
            print(f'CVF: No vehicles found, spawining a new one')
            vehicle: Optional[carla.Vehicle] = None
            while vehicle is None:
                vehicle = self.make_vehicle(True)
                time.sleep(0.5)
                
            self.configure_ego_car(vehicle)
            
            return (vehicle, True)
        else:
            print(f'CVF: Found a vehicle, attaching the mirror')
            vehicle = cast(carla.Vehicle, vehicles[0])
            return (vehicle, False)

    def make_vehicle(self,
                     is_ego_car: bool,
                     transform: Optional[carla.Transform] = None) -> Optional[carla.Vehicle]:
        vehicle_bp: Optional[carla.ActorBlueprint] = None
        if is_ego_car:
            vehicle_bp = self.world.get_blueprint_library().filter(VehicleFactory.ego_car_type)[0]
            vehicle_bp.set_attribute('role_name', 'ego')
        else:
            vehicles_bps = self.world.get_blueprint_library().filter('vehicle.*')
            vehicles_bps = [
                bp for bp in vehicles_bps if 
                    bp.id in PASSENGE_CARS
                    and bp.has_attribute('number_of_wheels')
                    and int(bp.get_attribute('number_of_wheels')) == 4
            ]
            vehicle_bp = random.choice(vehicles_bps)
            
            while vehicle_bp.id == VehicleFactory.ego_car_type:
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

        try:
            vehicle = cast(carla.Vehicle, self.world.spawn_actor(vehicle_bp, transform))
            vehicle.set_autopilot(True)
        except Exception as e:
            print(e)
            return None
        
        return vehicle

    def configure_traffic_vehicle(self,
                                  vehicle: carla.Vehicle) -> None:
        if self.traffic_manager:
            self.traffic_manager.vehicle_percentage_speed_difference(vehicle, -20)
            self.traffic_manager.ignore_lights_percentage(vehicle, 100)
            self.traffic_manager.ignore_signs_percentage(vehicle, 100)
            #self.traffic_manager.random_left_lanechange_percentage(vehicle, 20)
            #self.traffic_manager.random_right_lanechange_percentage(vehicle, 20)
   
    def configure_ego_car(self,
                   vehicle: carla.Vehicle) -> None:
        if self.traffic_manager:
            self.traffic_manager.ignore_lights_percentage(vehicle, 100)
            # self.traffic_manager.keep_right_rule_percentage(vehicle, 50)
        