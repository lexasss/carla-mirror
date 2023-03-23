from queue import Queue
from typing import Callable, List, Union, Any, Tuple

try:
    import carla
except ImportError:
    raise RuntimeError('cannot import CARLA')

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
        self.world = world
        self.sensors = sensors
        self.delta_seconds = 1.0 / fps

        self._can_tick_world = ticks
        self._queues: List[Queue[QueryResult]] = []
        
    def __enter__(self):
        self._settings = self.world.get_settings()
        self._frame = self.world.apply_settings(carla.WorldSettings(
            no_rendering_mode = False,
            synchronous_mode = True,
            fixed_delta_seconds = self.delta_seconds))

        def make_queue(register_event: Callable[[Callable[[QueryResult], None]], Any]) -> None:
            q: Queue[QueryResult] = Queue()
            register_event(q.put)
            self._queues.append(q)

        make_queue(self.world.on_tick)
        for sensor in self.sensors:
            make_queue(sensor.listen)
        return self
    
    def __exit__(self, *sensors: Tuple[carla.Sensor]):
        self.world.apply_settings(self._settings)

    def tick(self, timeout: float) -> List[QueryResult]:
        if self._can_tick_world:
            self._frame = self.world.tick()
            data = [self._retrieve_data(q, timeout) for q in self._queues]
        else:
            # we are forced to ignore the frame number here, as we are not allowed to call world.tick()
            data = [q.get(timeout = timeout) for q in self._queues]
        #assert all(x.frame == self.frame for x in data)
        return data

    def _retrieve_data(self, sensor_queue: 'Queue[QueryResult]', timeout: float) -> QueryResult:
        while True:
            data = sensor_queue.get(timeout = timeout)
            if data.frame == self._frame:
                return data
