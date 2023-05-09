import random

from typing import Optional, List

from queue import SimpleQueue

from src.user_action import Action, ActionType, DriverTask, CarSpawningLocation

from src.exp.task_screen import TaskScreenRequests, TaskScreenRequest, TaskScreen
from src.exp.logging import Logger
from src.exp.delayed_task import DelayedTask
from src.exp.mirror_status import MirrorStatus, NetCmd

from src.net.tcp_server import TcpServer
from src.net.tcp_client import TcpClient

REPETITIONS = 5
DISTANCES = [5, 15, 25]
SPAWN_VEHICLE_BEHIND = 30 # meters
SPAWN_LOCATIONS = [
    CarSpawningLocation.behind_next_lane,
    CarSpawningLocation.behind_same_lane,
    CarSpawningLocation.random,
]
SPAWN_PAUSE = 10.0

class Scenario:
    def __init__(self,
                 task_screen: TaskScreen,
                 cmd_server: Optional[TcpServer],
                 cmd_client: Optional[TcpClient],
                 mirror_status: MirrorStatus) -> None:
        
        self.search_target_distance = 0.0
        
        self._mirror_status = mirror_status

        self._task_screen = task_screen
        self._task_screen.set_callback(lambda request: self._task_screen_requests.put(request))
        
        self._task_screen_requests: SimpleQueue[TaskScreenRequest] = SimpleQueue()
        self._controller_actions: SimpleQueue[Action] = SimpleQueue()

        self._delayed_tasks: List[DelayedTask] = list()

        self._logger = Logger('scenario')
        
        self._task_distances: List[float] = []
        self._task_distance_index = -1
        self._task_distance = 0
        self._task_waiting_for_reply = False
        
        for _ in range(REPETITIONS):
            for dist in DISTANCES:
                self._task_distances.append(dist)
        
        random.shuffle(self._task_distances)
        
        self._car_spawning_location_index = 0

        self._cmd_server = cmd_server
        self._cmd_client = cmd_client
        
        self._is_running = False
        
    def start(self) -> None:
        self._is_running = True
        
        self._next_task()
        self._delayed_tasks.append(DelayedTask(1.0, self._spawn_random_target))
        self._delayed_tasks.append(DelayedTask(2.0, self._spawn_next_car))
        
    def tick(self) -> None:
        finished_tasks = [task for task in self._delayed_tasks if task.tick()]
        for task in finished_tasks:
            self._delayed_tasks.remove(task)
            
        while not self._task_screen_requests.empty():
            request = self._task_screen_requests.get()
            if request.req == TaskScreenRequests.target_noticed:
                self._logger.log('target', 'noticed', f'{self.search_target_distance:.1f}')
                self._spawn_random_target()
            elif request.req == TaskScreenRequests.lane_change_evaluated:
                # we got a response to the questionnaire, lets resume driving
                self._logger.log('evaluation', 'response', request.param)
                self._task_waiting_for_reply = False
                self._controller_actions.put(Action(ActionType.UNFREEZE))

                if self._next_task():
                    self._delayed_tasks.append(DelayedTask(2.0, self._spawn_next_car))
                else:
                    self._clear_tasks()

                    self._delayed_tasks.append(DelayedTask(0.3, self._task_screen.show_message, 'Done!\nThank you!'))
                    self._delayed_tasks.append(DelayedTask(1.5, self._controller_actions.put, Action(ActionType.STOP_SCENARIO)))

                    self._logger.log('done')
                    self._is_running = False
                
                self._delayed_tasks.append(DelayedTask(0.5, self._task_screen.hide_questionnaire))
                self._delayed_tasks.append(DelayedTask(1.0, self._continue_driving))
            else:
                print(f'SCN: unknown request: {request.req} ({request.param})')
    
    def get_action(self) -> Optional[Action]:
        if not self._controller_actions.empty():
            result = self._controller_actions.get()
            print(f'SCN: action {result.type} ({result.param})')
            return result
        
    def set_nearest_vehicle_behind(self, name: str, disatnce: float, lane: str) -> bool:
        if not self._is_running:
            return False
        
        if not self._task_waiting_for_reply:
            if abs(disatnce - self._task_distance) < 0.5:   # we compare against some range, i.e. plus-minus N, not exact N = 0
                self._clear_tasks()

                self._task_waiting_for_reply = True
                self._task_screen.show_questionnaire()
                
                self._controller_actions.put(Action(ActionType.REMOVE_CARS))
                self._controller_actions.put(Action(ActionType.FREEZE))
                
                name = '_'.join(name.split('.')[1:])
                self._logger.log('car', 'approached', name, lane, f'{disatnce:.1f}')
                self._logger.log('evaluation', 'request')
                
                if self._cmd_server:
                    self._cmd_server.send(NetCmd.hide_mirror)

                self._delayed_tasks.append(DelayedTask(0.1, self._stop_driving))
                
                return True
            
        return False
    
    def report_action_result(self, action: Action, has_spawned: bool):
        if not self._is_running:
            return
        
        if action.type == ActionType.SPAWN_CAR:
            if has_spawned:
                location = SPAWN_LOCATIONS[self._car_spawning_location_index]
                self._logger.log('car', 'spawned', location)
                
                self._car_spawning_location_index += 1
                if self._car_spawning_location_index == len(SPAWN_LOCATIONS):
                    self._car_spawning_location_index = 0
                    
                self._delayed_tasks.append(DelayedTask(SPAWN_PAUSE, self._spawn_next_car))
            else:
                self._delayed_tasks.append(DelayedTask(1.0, self._spawn_next_car))
                
    
    # Internal

    def _spawn_random_target(self) -> None:
        target_id = random.choice([x for x in DriverTask.TARGETS])

        name = '_'.join(target_id.split('.')[1:])
        self._logger.log('target', 'spawned', name)

        self._controller_actions.put(Action(ActionType.SPAWN_TARGET, target_id))
        self._delayed_tasks.append(DelayedTask(1.0, self._task_screen.show_message, f'Please find "{DriverTask.TARGETS[target_id]}"'))
        
    def _spawn_next_car(self) -> None:
        param = (SPAWN_LOCATIONS[self._car_spawning_location_index], SPAWN_VEHICLE_BEHIND)
        self._controller_actions.put(Action(ActionType.SPAWN_CAR, param))
        
    def _next_task(self):
        self._task_distance_index += 1
        if self._task_distance_index == len(self._task_distances):
            return False
        
        self._task_distance = self._task_distances[self._task_distance_index]
        self._logger.log('task', 'created', self._task_distance)
        
        return True
        
    def _stop_driving(self) -> None:
        self._mirror_status.is_frozen = True
        
    def _continue_driving(self) -> None:
        self._mirror_status.is_frozen = False
        if self._cmd_server:
            self._cmd_server.send(NetCmd.show_mirror)
        
    def _clear_tasks(self) -> None:
        print(f'Cancelling {len(self._delayed_tasks)} tasks')
        for task in self._delayed_tasks:
            task.cancel()
        self._delayed_tasks.clear()
