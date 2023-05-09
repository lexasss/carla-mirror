# Based on a script by:
# Copyright (c) 2021 Computer Vision Center (CVC) at the Universitat Autonoma de Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

from queue import Queue, Empty
from typing import Callable, List, Union, Any, Tuple, Optional

import carla

QueryResult = Union[carla.WorldSnapshot, carla.SensorData]

class CarlaSyncMode(object):
    '''
    Context manager to synchronize output from different sensors. Synchronous
    mode is enabled as long as we are inside this context

        with CarlaSyncMode(world, sensors) as sync_mode:
            while True:
                data = sync_mode.tick(timeout=1.0)

    '''
    def __init__(self,
                 world: carla.World,
                 fps: int = 30,
                 ticks: bool = False,       # only one client can call world.tick()
                 *sensors: carla.Sensor):
        self._world = world
        self._sensors = sensors
        
        self._delta_seconds = 1.0 / fps
        self._can_tick_world = ticks
        self._queues: List[Queue[QueryResult]] = []
        self._frame: int = 0
        
    def __enter__(self):
        self._settings = self._world.get_settings()
        self._frame = self._world.apply_settings(carla.WorldSettings(
            no_rendering_mode = False,
            synchronous_mode = True,
            fixed_delta_seconds = self._delta_seconds))

        def make_queue(register_event: Callable[[Callable[[QueryResult], None]], Any]) -> None:
            q: Queue[QueryResult] = Queue()
            register_event(q.put)
            self._queues.append(q)

        make_queue(self._world.on_tick)
        for sensor in self._sensors:
            make_queue(sensor.listen)
            
        return self
    
    def __exit__(self, *sensors: Tuple[carla.Sensor]):
        self._world.apply_settings(self._settings)

    def tick(self, timeout: float) -> Optional[List[QueryResult]]:
        if self._can_tick_world:
            self._frame = self._world.tick()
            data = [self._retrieve_data(q, timeout) for q in self._queues]
        else:
            # we are forced to ignore the frame number here, as we are not allowed to call world.tick()
            try:
                data = [q.get(timeout = timeout) for q in self._queues]
            except Empty:
                return None
            
        #assert all(x.frame == self.frame for x in data)
        return data

    # Internal
    
    def _retrieve_data(self, sensor_queue: 'Queue[QueryResult]', timeout: float) -> QueryResult:
        while True:
            data = sensor_queue.get(timeout = timeout)
            if data.frame == self._frame:
                return data
