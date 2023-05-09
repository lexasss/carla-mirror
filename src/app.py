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

from src.exp.logging import Logger
from src.exp.scenario import Scenario
from src.exp.task_screen import TaskScreen
from src.exp.mirror_status import MirrorStatus

from src.net.tcp_server import TcpServer
from src.net.tcp_client import TcpClient

class Finished(Exception):
    pass

class App:
    
    def __init__(self):
        self._spawned_actors: List[carla.Actor] = []
        
        self._logger = Logger('app')
        
        CarlaEnvironment.set_driver_offset(VehicleFactory.EGO_CAR_TYPE)
        SideMirror.set_camera_offset(VehicleFactory.EGO_CAR_TYPE)
        FullscreenMirror.set_camera_offset(VehicleFactory.EGO_CAR_TYPE)
        WideviewMirror.set_camera_offset(VehicleFactory.EGO_CAR_TYPE)
        
    def run(self):
        settings = Settings()

        pygame.init()

        client = carla.Client(settings.host, 2000)
        client.set_timeout(5.0)
        
        try:
            environment = CarlaEnvironment(client, settings)
            world = environment.load_world(settings.town)

        except:
            print(f'APP: CARLA is not running')
            mirror = self._create_mirror(settings)
            self._show_blank_mirror(mirror, settings.server_host)

        else:
            runner: Optional[Runner] = None
            
            vehicle_factory = VehicleFactory(client)
            ego_car, is_ego_car_created = vehicle_factory.get_ego_car()

            mirror = self._create_mirror(settings, world, ego_car)

            if is_ego_car_created:
                mirror_name = str(settings.side).split('.')[1].lower()
                self._logger.log('mirror', mirror_name)
                car_name = '_'.join(ego_car.type_id.split('.')[1:])
                self._logger.log('car', car_name)
                
                self._spawned_actors.append(ego_car)
                
                runner = Runner(environment, vehicle_factory, ego_car, mirror)

            if mirror.camera:
                self._spawned_actors.append(mirror.camera)
                
            self._show_carla_mirror(mirror, runner, settings.server_host)

        finally:
            for actor in self._spawned_actors:
                actor.destroy()

            pygame.quit()

    # Internal

    def _run_loop(self,
                 sync_mode: CarlaSyncMode,
                 mirror: Mirror,
                 runner: Optional[Runner],
                 server_host: Optional[str]):
        clock = pygame.time.Clock()

        tcp_server = TcpServer() if runner else None
        tcp_client = TcpClient(server_host) if server_host else None
        task_screen = TaskScreen() if runner else None
        
        mirror_status = MirrorStatus()
        scenario = Scenario(task_screen, tcp_server, tcp_client, mirror_status) if task_screen else None
        
        if tcp_server:
            tcp_server.start()
        if tcp_client:
            tcp_client.connect(mirror_status.handle_net_request)

        try:
            while True:
                action = UserAction.get()
                
                if scenario:
                    scenario.tick()
                    if action is None: 
                        action = scenario.get_action()
                        
                self._handle_action(action, mirror, scenario, runner)

                mirror_image: Optional[carla.Image] = None
                spawned: Optional[carla.Actor] = None
                
                if not mirror_status.is_frozen:
                    # Advance the simulation and wait for the data.
                    queries = sync_mode.tick(5.0)
                    if queries:
                        snapshot, image = queries
                        mirror_image = cast(carla.Image, image)
                    
                        if runner:
                            carla_snapshot = cast(carla.WorldSnapshot, snapshot)
                            spawned = runner.make_step(carla_snapshot, action)
                            
                            if scenario:
                                self._update_scenario_state(scenario, runner, carla_snapshot.find(runner.ego_car.id))
                                if action:
                                    scenario.report_action_result(action, spawned is not None)

                if spawned:
                    self._spawned_actors.append(spawned)

                mirror.draw_image(mirror_image)
                
                pygame.display.flip()
                
                clock.tick(CarlaEnvironment.FPS)
        except Finished:
            pass
            
        if task_screen:
            task_screen.close()
        if tcp_server:
            tcp_server.close()
        if tcp_client:
            tcp_client.close()
        
        self._remove_spawned(sync_mode)

    def _show_carla_mirror(self,
                           mirror: Mirror,
                           runner: Optional[Runner],
                           server_host: Optional[str]):
        try:
            with CarlaSyncMode(cast(carla.World, mirror.world),
                            CarlaEnvironment.FPS,
                            runner is not None,
                            cast(carla.Sensor, mirror.camera)) as sync_mode:     # Create a synchronous mode context.
                self._run_loop(sync_mode, mirror, runner, server_host)
        finally:
            time.sleep(0.5)

    def _show_blank_mirror(self,
                           mirror: Mirror,
                           server_host: Optional[str]):
        clock = pygame.time.Clock()

        tcp_server = TcpServer() if not server_host else None
        tcp_client = TcpClient(server_host) if server_host else None
        task_screen = TaskScreen() if not server_host else None
        
        mirror_status = MirrorStatus()
        scenario = Scenario(task_screen, tcp_server, tcp_client, mirror_status) if task_screen else None
        
        if not scenario and tcp_client:
            tcp_client.connect(mirror_status.handle_net_request)

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
                elif action.type == ActionType.DEBUG_TCP:
                    if tcp_client:
                        tcp_client.request('test\n')
            elif scenario:
                action = scenario.get_action()
            
            mirror.draw_image(None)
            
            pygame.display.flip()
            clock.tick(CarlaEnvironment.FPS)

        if task_screen:
            task_screen.close()
        if tcp_server:
            tcp_server.close()
        if tcp_client:
            tcp_client.close()

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
        scenario.search_target_distance = runner.get_distance_to_search_target(ego_car_snapshot)
        vehicle, distance, lane = runner.get_nearest_vehicle_behind(ego_car_snapshot)
        if vehicle and lane:
            scenario.set_nearest_vehicle_behind(vehicle.type_id, distance, lane)
        
    def _remove_spawned(self, sync_mode: CarlaSyncMode):
        actors = [x for x in self._spawned_actors if not x.type_id.startswith('sensor.')]
        self._spawned_actors = [x for x in self._spawned_actors if x.type_id.startswith('sensor.')]
        
        for actor in actors:
            actor.destroy()
            sync_mode.tick(5.0)
