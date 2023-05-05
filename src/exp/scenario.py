import random
import time

from typing import Optional, Callable, List, Any

from queue import SimpleQueue

from src.user_action import Action, ActionType, DriverTask, CarSpawningLocation

from src.exp.remote import RemoteRequests, RemoteRequest, Remote
from src.exp.logging import Logger

DISTANCES = [25, 25, 25]
SPAWN_LOCATIONS = [
    CarSpawningLocation.behind_next_lane,
    CarSpawningLocation.behind_next_lane,
    CarSpawningLocation.behind_same_lane,
    CarSpawningLocation.random,
    CarSpawningLocation.behind_next_lane,
    CarSpawningLocation.behind_same_lane,
    CarSpawningLocation.random,
]
SPAWN_PAUSE = 10.0

class DelayedTask:
    def __init__(self, delay: float, cb: Callable[..., None], *args: Any, is_repetitive: bool = False) -> None:
        self._cb = cb
        self._args = args
        self._delay = delay
        self._start = time.perf_counter()
        self._is_active = True
        self._is_repetitive = is_repetitive

    def tick(self) -> bool:
        if (time.perf_counter() - self._start) > self._delay:
            if self._is_active:
                self._cb(*self._args)
                self._is_active = self._is_repetitive
            
            if self._is_active:
                self._start = time.perf_counter()
                
            return True
        
        return False
    
    def cancel(self) -> None:
        self._is_active = False
    
class Scenario:
    def __init__(self, remote: Remote) -> None:
        
        self.search_target_distance = 0.0
        
        self._remote = remote
        self._remote.set_callback(lambda request: self._remote_requests.put(request))
        
        self._remote_requests: SimpleQueue[RemoteRequest] = SimpleQueue()
        self._controller_actions: SimpleQueue[Action] = SimpleQueue()

        self._delayed_tasks: List[DelayedTask] = list()

        self._logger = Logger('scenario')
        
        self._task_distances = DISTANCES
        self._task_distance_index = -1
        self._task_distance = 0
        self._task_waiting_for_reply = False
        self._task_displays_frozen = False
        
        self._car_spawning_location_index = 0
        
        self._is_running = False
        
    def is_driving_enabled(self) -> bool:
        return not self._task_displays_frozen
    
    def start(self) -> None:
        self._is_running = True
        
        self._next_task()
        self._delayed_tasks.append(DelayedTask(1.0, self._spanw_random_target))
        self._delayed_tasks.append(DelayedTask(2.0, self._spanw_next_car))
        
    def tick(self) -> None:
        if not self._is_running:
            return
        
        finished_tasks = [task for task in self._delayed_tasks if task.tick()]
        for task in finished_tasks:
            self._delayed_tasks.remove(task)
            
        while not self._remote_requests.empty():
            request = self._remote_requests.get()
            if request.req == RemoteRequests.target_noticed:
                self._logger.log('target', 'noticed', f'{self.search_target_distance:.1f}')
                self._spanw_random_target()
            elif request.req == RemoteRequests.lane_change_evaluated:
                # we got a response to the questionnaire, lets resume driving
                self._logger.log('evaluation', 'response', request.param)
                self._task_waiting_for_reply = False
                self._controller_actions.put(Action(ActionType.UNFREEZE))

                if self._next_task():
                    self._delayed_tasks.append(DelayedTask(2.0, self._spanw_next_car))
                else:
                    self._clear_tasks()
                    
                    self._delayed_tasks.append(DelayedTask(1.5, self._controller_actions.put, Action(ActionType.STOP_SCENARIO)))
                    self._is_running = False
                
                self._delayed_tasks.append(DelayedTask(0.3, self._remote.hide_questionnaire))
                self._delayed_tasks.append(DelayedTask(1.0, self._continue_driving))
            else:
                print(f'SCN: unknown request: {request.req} ({request.param})')
    
    def get_action(self) -> Optional[Action]:
        if not self._controller_actions.empty():
            result = self._controller_actions.get()
            print(f'SCN: action {result.type} ({result.param})')
            return result
        
    def set_nearest_vehicle_behind(self, disatnce: float) -> bool:
        if not self._task_waiting_for_reply:
            if abs(disatnce - self._task_distance) < 0.5:
                self._clear_tasks()

                self._task_waiting_for_reply = True
                self._remote.show_questionnaire()
                
                self._controller_actions.put(Action(ActionType.REMOVE_CARS))
                self._controller_actions.put(Action(ActionType.FREEZE))
                
                self._logger.log('evaluation', 'request')
                
                self._delayed_tasks.append(DelayedTask(0.1, self._stop_driving))
                
                return True
            
        return False
    
    def report_action_result(self, action: Action, has_spawned: bool):
        if action.type == ActionType.SPAWN_CAR:
            if has_spawned:
                location = SPAWN_LOCATIONS[self._car_spawning_location_index]
                self._logger.log('car', 'spawned', location)
                
                self._car_spawning_location_index += 1
                if self._car_spawning_location_index == len(SPAWN_LOCATIONS):
                    self._car_spawning_location_index = 0
                    
                self._delayed_tasks.append(DelayedTask(SPAWN_PAUSE, self._spanw_next_car))
            else:
                self._delayed_tasks.append(DelayedTask(1.0, self._spanw_next_car))
                
    
    # Internal

    def _spanw_random_target(self) -> None:
        target_id = random.choice([x for x in DriverTask.TARGETS])
        self._logger.log('target', 'spawned', target_id)
        self._controller_actions.put(Action(ActionType.SPAWN_TARGET, target_id))
        self._delayed_tasks.append(DelayedTask(1.0, self._remote.show_message, f'Please find "{DriverTask.TARGETS[target_id]}"'))
        
    def _spanw_next_car(self) -> None:
        location = SPAWN_LOCATIONS[self._car_spawning_location_index]
        self._controller_actions.put(Action(ActionType.SPAWN_CAR, location))
        
    def _next_task(self):
        self._task_distance_index += 1
        if self._task_distance_index == len(self._task_distances):
            self._delayed_tasks.append(DelayedTask(1.0, self._remote.show_message, 'Done!\nThank you!'))
            self._logger.log('done')
            return False
        
        self._task_distance = self._task_distances[self._task_distance_index]
        self._logger.log('task', 'created', self._task_distance)
        
        return True
        
    def _stop_driving(self) -> None:
        self._task_displays_frozen = True
        
    def _continue_driving(self) -> None:
        self._task_displays_frozen = False
        
    def _clear_tasks(self) -> None:
        print(f'Cancelling {len(self._delayed_tasks)} tasks')
        for task in self._delayed_tasks:
            task.cancel()
        self._delayed_tasks.clear()
