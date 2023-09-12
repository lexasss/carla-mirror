from src.carla.utils import add_carla_path
add_carla_path()

from typing import Optional, List, cast

try:
    import carla
except ImportError:
    raise RuntimeError('cannot import CARLA')

from src.common.utils import suppress_stdout

try:
    with suppress_stdout():
        import pygame
except ImportError:
    raise RuntimeError('pygame is not installed')

import time

from src.common.user_action import UserAction, ActionType, Action
from src.common.settings import Settings, MirrorType
from src.runner import Runner

from src.carla.sync_mode import CarlaSyncMode
from src.carla.environment import CarlaEnvironment
from src.carla.vehicle_factory import VehicleFactory
from src.carla.monitor import CarlaMonitor

from src.mirror.side import SideMirror
from src.mirror.wideview import WideviewMirror
from src.mirror.top_view import TopViewMirror
from src.mirror.rectangular import RectangularMirror
from src.mirror.base import Mirror

from src.exp.scenario import Scenario
from src.exp.scenario_env import ScenarioEnvironment
from src.exp.traffic_state import TrafficState

from src.common.logging import EventLogger

class Finished(Exception):
    pass

class App:
    
    def __init__(self):
        self._spawned_actors: List[carla.Actor] = []
        
    def run(self):
        settings = Settings()

        VehicleFactory.set_driving_mode(settings.is_manual_mode)
        
        CarlaEnvironment.set_driver_offset(VehicleFactory.ego_car_type)
        SideMirror.set_camera_offset(VehicleFactory.ego_car_type)
        RectangularMirror.set_camera_offset(VehicleFactory.ego_car_type)
        WideviewMirror.set_camera_offset(VehicleFactory.ego_car_type)
        
        pygame.init()

        self._logger = EventLogger('app')
        
        client = carla.Client(settings.host, 2000)
        client.set_timeout(5.0)
        
        try:
            environment = CarlaEnvironment(client)
            world = environment.load_world(settings.town)

        except:
            print(f'APP: CARLA is not running')
            mirror = self._create_mirror(settings)
            self._show_blank_mirror(mirror)

        else:
            runner: Optional[Runner] = None
            
            vehicle_factory = VehicleFactory(client)
            ego_car, is_ego_car_created = vehicle_factory.get_ego_car()

            mirror = self._create_mirror(settings, world, ego_car)

            if is_ego_car_created or settings.adopt_egocar:
                mirror_name = str(settings.type).split('.')[1].lower()
                self._logger.log('mirror', mirror_name)
                car_name = '_'.join(ego_car.type_id.split('.')[1:])
                self._logger.log('car', car_name)
                
                if is_ego_car_created:
                    self._spawned_actors.append(ego_car)
                
                runner = Runner(environment, vehicle_factory, ego_car, mirror)

            if mirror.camera:
                self._spawned_actors.append(mirror.camera)
                
            self._monitor = CarlaMonitor(world)
            self._traffic_state = TrafficState()
            
            self._show_carla_mirror(mirror, runner, settings.scenario)

        finally:
            for actor in self._spawned_actors:
                actor.destroy()

            pygame.quit()

    # Internal

    def _run_loop(self,
                 sync_mode: CarlaSyncMode,
                 mirror: Mirror,
                 runner: Optional[Runner],
                 env: ScenarioEnvironment,
                 timeout: float):
                
        clock = pygame.time.Clock()
        scenario = env.scenario if env is not None else None

        while True:
            action = UserAction.get()
            
            if scenario:
                scenario.tick()
                if action is None: 
                    action = scenario.get_action()
                    
            self._handle_action(action, mirror, scenario, runner)

            mirror_image: Optional[carla.Image] = None
            spawned: Optional[carla.Actor] = None
            
            avoid_drawing_reflection = env is not None and env.mirror_status.is_frozen
            if not avoid_drawing_reflection:
                # Advance the simulation and wait for the data.
                queries = sync_mode.tick(timeout)
                if queries:
                    snapshot, image = queries
                    mirror_image = cast(carla.Image, image)
                    
                    if runner:
                        world_snapshot = cast(carla.WorldSnapshot, snapshot)
                        ego_car_snapshot, spawned = runner.make_step(world_snapshot, action)
                        
                        if scenario:
                            self._update_scenario_state(scenario, runner, ego_car_snapshot)
                            if action:
                                scenario.report_action_result(action, spawned is not None)

            if spawned:
                self._spawned_actors.append(spawned)

            mirror.draw_image(mirror_image)
            
            pygame.display.flip()
            
            clock.tick(CarlaEnvironment.FPS)

    def _show_carla_mirror(self,
                           mirror: Mirror,
                           runner: Optional[Runner],
                           scenario: Optional[str]):
        try:
            with CarlaSyncMode(cast(carla.World, mirror.world),
                            CarlaEnvironment.FPS,
                            runner is not None,
                            cast(carla.Sensor, mirror.camera)) as sync_mode:     # Create a synchronous mode context.
                try:
                    if scenario is not None:
                        with ScenarioEnvironment(runner is not None) as env:
                            self._run_loop(sync_mode, mirror, runner, env, timeout=5.0)
                    else:
                        self._run_loop(sync_mode, mirror, runner, env=None, timeout=0.2)
                except Finished:
                    pass
            
            self._remove_spawned(sync_mode)

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
                    elif action.type == ActionType.MIRROR_VIEW_OFFSET:
                        mirror.on_offset(cast(str, action.param))
                    elif action.type == ActionType.DEBUG_MIRROR:
                        if action.param == 'snapshot':
                            mirror.save_snapshot('debug')
                    elif action.type == ActionType.DEBUG_TASK_SCREEN:
                        if scenario:
                            scenario.report_action_result(action, False)
                elif scenario:
                    action = scenario.get_action()
                
                mirror.draw_image(None)
                
                pygame.display.flip()
                clock.tick(CarlaEnvironment.FPS)

    def _create_mirror(self, settings: Settings, world: Optional[carla.World] = None, ego_car: Optional[carla.Vehicle] = None) -> Mirror:
        if settings.type == MirrorType.WIDEVIEW:
            return WideviewMirror(settings, world, ego_car)
        elif settings.type == MirrorType.TOPVIEW:
            return TopViewMirror(settings, world, ego_car)
        elif settings.type == MirrorType.RLEFT or settings.type == MirrorType.RRIGHT or settings.type == MirrorType.RREAR:
            return RectangularMirror(settings, world, ego_car)
        elif settings.type == MirrorType.LEFT or settings.type == MirrorType.RIGHT:
            return SideMirror(settings, world, ego_car)
        else:
            print(f'APP Unknown mirror type: "{settings.type}"')
            raise IndexError

    def _handle_action(self,
                       action: Optional[Action],
                       mirror: Mirror,
                       scenario: Optional[Scenario],
                       runner: Optional[Runner]) -> None:
        if not action:
            return
        
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
        elif action.type == ActionType.DEBUG_MIRROR:
            if action.param == 'snapshot':
                self._print_image(mirror, True)

    def _update_scenario_state(self,
                               scenario: Scenario,
                               runner: Runner,
                               ego_car_snapshot: carla.ActorSnapshot) -> None:
        if runner.search_target is None:
            scenario.set_search_target_distance(0)
        else:
            scenario.set_search_target_distance(runner.controller.get_distance_to(ego_car_snapshot, runner.search_target))
        
        car_behind, all_distances = self._monitor.get_nearest_vehicle_behind(ego_car_snapshot)
        
        self._traffic_state.reset()
        self._traffic_state.ego_car_lane_props = self._monitor.get_lane_props(ego_car_snapshot)
        self._traffic_state.update(all_distances)
        self._traffic_state.log()

        if car_behind is not None:
            if scenario.set_nearest_vehicle_behind(car_behind.vehicle.type_id, car_behind.distance, car_behind.lane, runner.ego_car_speed):
                runner.mirror.save_snapshot(f'{car_behind.lane}_{car_behind.distance:.0f}')
        
    def _remove_spawned(self, sync_mode: CarlaSyncMode):
        actors = [x for x in self._spawned_actors if not x.type_id.startswith('sensor.')]
        self._spawned_actors = [x for x in self._spawned_actors if x.type_id.startswith('sensor.')]
        
        for actor in actors:
            actor.destroy()
            sync_mode.tick(5.0)

    def _print_image(self, mirror: Mirror, at_any_distance: bool = False):
        if mirror.world:
            ego_car = mirror.world.get_actors().filter(VehicleFactory.ego_car_type)[0]
            snapshot = mirror.world.get_snapshot()
            ego_car_snapshot = snapshot.find(ego_car.id)
            _, distance, _ = self._monitor.get_nearest_vehicle_behind(ego_car_snapshot)
            if at_any_distance:
                if distance < 50:
                    mirror.save_snapshot(f'{distance:.1f}')
                    
            # Uncomment and edit next lines to grab iages automatically under certain conditions
            
            # elif 15.0 < distance and distance < 15.3:
            #     if lane == 'same':
            #         mirror.save_snapshot(f'{distance:.1f}')
            # elif mirror.type == 'rleft' and 40.0 < distance and distance < 40.2:
            #     mirror.save_snapshot(f'{distance:.1f}')
        