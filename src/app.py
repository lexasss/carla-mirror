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

from src.controller import Controller, ActionType
from src.settings import Settings, Side
from src.runner import Runner
from src.carla_sync_mode import CarlaSyncMode
from src.environment import Environment
from src.vehicle_factory import VehicleFactory
from src.mirror.side import SideMirror
from src.mirror.wideview import WideviewMirror
from src.mirror.fullscreen import FullscreenMirror
from src.mirror.base import Mirror


class App:
    
    def __init__(self):
        self.spawned_actors: List[carla.Actor] = []
        
        Environment.set_driver_offset(VehicleFactory.EGO_CAR_TYPE)
        SideMirror.set_camera_offset(VehicleFactory.EGO_CAR_TYPE)
        FullscreenMirror.set_camera_offset(VehicleFactory.EGO_CAR_TYPE)

    def run(self):
        settings = Settings()

        pygame.init()

        client = carla.Client(settings.host, 2000)
        client.set_timeout(5.0)
        
        try:
            environment = Environment(client, settings)
            world = environment.load_world(settings.town)

        except:
            print(f'CARLA is not running')
            mirror = self._create_mirror(settings)
            self.show_blank_mirror(mirror)

        else:
            runner: Optional[Runner] = None
            
            vehicle_factory = VehicleFactory(client)
            ego_car, is_ego_car_created = vehicle_factory.get_ego_car()

            mirror = self._create_mirror(settings, world, ego_car)

            if is_ego_car_created:
                self.spawned_actors.append(ego_car)
                runner = Runner(environment, vehicle_factory, ego_car, mirror)

            if mirror.camera is not None:
                self.spawned_actors.append(mirror.camera)
                
            # create_traffic(world)      # why they are all crashing if spawned at once when we exit from this script?
            
            self.show_carla_mirror(mirror, runner)

        finally:
            for actor in self.spawned_actors:
                actor.destroy()

            pygame.quit()

    # Internal

    def run_loop(self,
                 sync_mode: CarlaSyncMode,
                 mirror: Mirror,
                 runner: Optional[Runner]):
        clock = pygame.time.Clock()

        while True:
            action = Controller.get_input()
            
            if action is not None:
                if action.type == ActionType.QUIT:
                    break
                elif action.type == ActionType.MOUSE:
                    mirror.on_mouse(action.param)

            # Advance the simulation and wait for the data.
            snapshot, image = sync_mode.tick(timeout = 5.0)
            
            if runner is not None:
                spawned = runner.make_step(cast(carla.WorldSnapshot, snapshot), action)
                if spawned is not None:
                    self.spawned_actors.append(spawned)

            mirror.draw_image(cast(carla.Image, image))
            
            pygame.display.flip()
            clock.tick(Environment.FPS)

    def show_carla_mirror(self, mirror: Mirror, runner: Optional[Runner] = None):
        try:
            with CarlaSyncMode(cast(carla.World, mirror.world),
                            Environment.FPS,
                            runner is not None,
                            cast(carla.Sensor, mirror.camera)) as sync_mode:     # Create a synchronous mode context.
                self.run_loop(sync_mode, mirror, runner)
        finally:
            time.sleep(0.5)

    def show_blank_mirror(self, mirror: Mirror):
        clock = pygame.time.Clock()

        while True:
            action = Controller.get_input()
            if action is not None:
                if action.type == ActionType.QUIT:
                    break
                elif action.type == ActionType.MOUSE:
                    mirror.on_mouse(action.param)
            
            mirror.draw_image(None)
            
            pygame.display.flip()
            clock.tick(Environment.FPS)

    def _create_mirror(self, settings: Settings, world: Optional[carla.World] = None, ego_car: Optional[carla.Vehicle] = None) -> Mirror:
        if settings.side == Side.WIDEVIEW:
            return WideviewMirror(settings, world, ego_car)
        elif settings.side == Side.FULLSCREEN:
            return FullscreenMirror(settings, world, ego_car)
        else:
            return SideMirror(settings, world, ego_car)
