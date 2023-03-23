import utils
utils.add_carla_path()

try:
    import carla
except ImportError:
    raise RuntimeError('cannot import CARLA')

try:
    with utils.suppress_stdout():
        import pygame
except ImportError:
    raise RuntimeError('pygame is not installed')

from controller import Controller, ActionType

import time

from typing import Optional, List, cast

from settings import Settings
from runner import Runner
from carla_sync_mode import CarlaSyncMode
from environment import Environment
from vehicle_factory import VehicleFactory
from mirror import Mirror


class App:
    
    def __init__(self):
        self.spawned_actors: List[carla.Actor] = []

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
            mirror.draw_mask()
            
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
            
            mirror.draw_mask()
            
            pygame.display.flip()
            clock.tick(Environment.FPS)

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
            mirror = Mirror(settings)
            self.show_blank_mirror(mirror)

        else:
            runner: Optional[Runner] = None
            
            vehicle_factory = VehicleFactory(client)
            ego_car, is_ego_car_created = vehicle_factory.get_ego_car()
            if is_ego_car_created:
                self.spawned_actors.append(ego_car)
                runner = Runner(environment, vehicle_factory, ego_car)

            mirror = Mirror(settings, world, ego_car)
            if mirror.camera is not None:
                self.spawned_actors.append(mirror.camera)
                
            # create_traffic(world)      # why they are all crashing if spawned at once when we exit from this script?
            
            self.show_carla_mirror(mirror, runner)

        finally:
            for actor in self.spawned_actors:
                actor.destroy()

            pygame.quit()

if __name__ == '__main__':
    try:
        App().run()
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')
    else:
        print('done.')
