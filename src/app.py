from src.utils import add_carla_path, suppress_stdout
add_carla_path()

from typing import Optional, List, cast

try:
    import carla
except ImportError:
    raise RuntimeError('cannot import CARLA')

try:
    with suppress_stdout():
        import pygame
except ImportError:
    raise RuntimeError('pygame is not installed')

import time

from src.user_action import UserAction, ActionType, Action
from src.settings import Settings, Side
from src.runner import Runner

from src.carla.sync_mode import CarlaSyncMode
from src.carla.environment import CarlaEnvironment
from src.carla.vehicle_factory import VehicleFactory

from src.mirror.side import SideMirror
from src.mirror.wideview import WideviewMirror
from src.mirror.top_view import TopViewMirror
from src.mirror.fullscreen import FullscreenMirror
from src.mirror.base import Mirror

from src.exp.logging import EventLogger
from src.exp.scenario import Scenario
from src.exp.scenario_env import ScenarioEnvironment

class Finished(Exception):
    pass

class App:
    
    def __init__(self):
        self._spawned_actors: List[carla.Actor] = []
        
        CarlaEnvironment.set_driver_offset(VehicleFactory.EGO_CAR_TYPE)
        SideMirror.set_camera_offset(VehicleFactory.EGO_CAR_TYPE)
        FullscreenMirror.set_camera_offset(VehicleFactory.EGO_CAR_TYPE)
        WideviewMirror.set_camera_offset(VehicleFactory.EGO_CAR_TYPE)
        
    def run(self):
        settings = Settings()

        pygame.init()

        self._logger = EventLogger('app')
        
        client = carla.Client(settings.host, 2000)
        client.set_timeout(5.0)
        
        try:
            environment = CarlaEnvironment(client, settings)
            world = environment.load_world(settings.map)

        except:
            print(f'APP: CARLA is not running')
            mirror = self._create_mirror(settings)
            self._show_blank_mirror(mirror)

        else:
            runner: Optional[Runner] = None
            
            vehicle_factory = VehicleFactory(client)
            ego_car, is_ego_car_created = vehicle_factory.get_ego_car()

            mirror = self._create_mirror(settings, world, ego_car)

            if is_ego_car_created or settings.is_primary_mirror:
                mirror_name = str(settings.side).split('.')[1].lower()
                self._logger.log('mirror', mirror_name)
                car_name = '_'.join(ego_car.type_id.split('.')[1:])
                self._logger.log('car', car_name)
                
                if is_ego_car_created:
                    self._spawned_actors.append(ego_car)
                
                runner = Runner(environment, vehicle_factory, ego_car, mirror)

            if mirror.camera:
                self._spawned_actors.append(mirror.camera)
                
            self._show_carla_mirror(mirror, runner)

        finally:
            for actor in self._spawned_actors:
                actor.destroy()

            pygame.quit()

    # Internal

    def _run_loop(self,
                 sync_mode: CarlaSyncMode,
                 mirror: Mirror,
                 runner: Optional[Runner]):
        clock = pygame.time.Clock()

        try:
            with ScenarioEnvironment(runner is not None) as env:
                scenario = env.scenario
                timeout = 5.0 if scenario else 0.2
                
                while True:
                    action = UserAction.get()
                    
                    if scenario:
                        scenario.tick()
                        if action is None: 
                            action = scenario.get_action()
                            
                    self._handle_action(action, mirror, scenario, runner)

                    mirror_image: Optional[carla.Image] = None
                    spawned: Optional[carla.Actor] = None
                    
                    if not env.mirror_status.is_frozen:
                        # Advance the simulation and wait for the data.
                        queries = sync_mode.tick(timeout)
                        if queries:
                            snapshot, image = queries
                            mirror_image = cast(carla.Image, image)
                        
                            if runner:
                                carla_snapshot = cast(carla.WorldSnapshot, snapshot)
                                ego_car_snapshot, spawned = runner.make_step(carla_snapshot, action)
                                
                                if scenario:
                                    self._update_scenario_state(scenario, runner, ego_car_snapshot)
                                    if action:
                                        scenario.report_action_result(action, spawned is not None)

                    if spawned:
                        self._spawned_actors.append(spawned)

                    mirror.draw_image(mirror_image)
                    
                    pygame.display.flip()
                    
                    clock.tick(CarlaEnvironment.FPS)
        except Finished:
            pass
            
        self._remove_spawned(sync_mode)

    def _show_carla_mirror(self,
                           mirror: Mirror,
                           runner: Optional[Runner]):
        try:
            with CarlaSyncMode(cast(carla.World, mirror.world),
                            CarlaEnvironment.FPS,
                            runner is not None,
                            cast(carla.Sensor, mirror.camera)) as sync_mode:     # Create a synchronous mode context.
                self._run_loop(sync_mode, mirror, runner)
        finally:
            time.sleep(0.5)

    def _show_blank_mirror(self, mirror: Mirror):
        clock = pygame.time.Clock()

        with ScenarioEnvironment() as env:
            scenario = env.scenario
        
            while True:
                action = UserAction.get()
                if scenario:
                    scenario.tick()

                if action:
                    if action.type == ActionType.QUIT:
                        break
                    elif action.type == ActionType.START_SCENARIO:
                        if scenario:
                            scenario.start()
                    elif action.type == ActionType.MOUSE:
                        mirror.on_mouse(cast(str, action.param))
                    elif action.type == ActionType.DEBUG_TASK_SCREEN:
                        if scenario:
                            scenario.report_action_result(action, False)
                elif scenario:
                    action = scenario.get_action()
                
                mirror.draw_image(None)
                
                pygame.display.flip()
                clock.tick(CarlaEnvironment.FPS)

    def _create_mirror(self, settings: Settings, world: Optional[carla.World] = None, ego_car: Optional[carla.Vehicle] = None) -> Mirror:
        if settings.side == Side.WIDEVIEW:
            return WideviewMirror(settings, world, ego_car)
        elif settings.side == Side.TOPVIEW:
            return TopViewMirror(settings, world, ego_car)
        elif settings.side == Side.FULLSCREEN:
            return FullscreenMirror(settings, world, ego_car)
        else:
            return SideMirror(settings, world, ego_car)

    def _handle_action(self,
                       action: Optional[Action],
                       mirror: Mirror,
                       scenario: Optional[Scenario],
                       runner: Optional[Runner]) -> None:
        if action:
            if action.type == ActionType.QUIT:
                raise Finished()
            elif action.type == ActionType.START_SCENARIO:
                if scenario:
                    scenario.start()
            elif action.type == ActionType.MOUSE:
                mirror.on_mouse(cast(str, action.param))
            elif action.type == ActionType.REMOVE_TARGETS:
                targets = [ x for x in self._spawned_actors if x.type_id.startswith('static.prop.') ]
                for target in targets:
                    self._spawned_actors.remove(target)
                    target.destroy()
            elif action.type == ActionType.REMOVE_CARS:
                ego_car = runner.ego_car if runner else None
                vehicles = [ x for x in self._spawned_actors if x.type_id.startswith('vehicle.') and x != ego_car ]
                for vehicle in vehicles:
                    self._spawned_actors.remove(vehicle)
                    vehicle.destroy()

    def _update_scenario_state(self,
                               scenario: Scenario,
                               runner: Runner,
                               ego_car_snapshot: carla.ActorSnapshot) -> None:
        if runner.search_target is None:
            scenario.search_target_distance = 0
        else:
            scenario.search_target_distance = runner.controller.get_distance_to(ego_car_snapshot, runner.search_target)
        
        monitor = runner.monitor
        vehicle, distance = monitor.get_nearest_vehicle_behind(ego_car_snapshot)
        if vehicle:
            lane = monitor.get_lane(ego_car_snapshot, vehicle)
            if lane:
                scenario.set_nearest_vehicle_behind(vehicle.type_id, distance, lane, runner.ego_car_speed)
        
    def _remove_spawned(self, sync_mode: CarlaSyncMode):
        actors = [x for x in self._spawned_actors if not x.type_id.startswith('sensor.')]
        self._spawned_actors = [x for x in self._spawned_actors if x.type_id.startswith('sensor.')]
        
        for actor in actors:
            actor.destroy()
            sync_mode.tick(5.0)
