import random
import time

from typing import Optional, List, cast

from queue import SimpleQueue

from src.exp.task_screen import TaskScreenRequests, TaskScreenRequest, TaskScreen
from src.exp.delayed_task import DelayedTask
from src.exp.mirror_status import MirrorStatus, NetCmd
from src.exp.scoring import Scoring

from src.net.tcp_server import TcpServer

from src.common.logging import EventLogger
from src.common.user_action import Action, ActionType, DriverTask, CarSpawningLocation

REPETITIONS = 6
DISTANCES = [5, 25, 40]
SPAWN_VEHICLE_BEHIND = 35 # meters
SPAWN_LOCATIONS = [
    CarSpawningLocation.behind_next_lane,
    CarSpawningLocation.behind_same_lane,
    CarSpawningLocation.random,
]
SPAWN_PAUSE = 10.0
MIN_EGOCAR_SPEED_TO_EVALUATE_LINE_CHANGE_SAFETY = 20.0
MAX_TARGET_LIFESPAN = 120.0     # 2 minutes

class Scenario:
    def __init__(self,
                 task_screen: TaskScreen,
                 cmd_server: Optional[TcpServer],
                 mirror_status: MirrorStatus) -> None:
        
        self._mirror_status = mirror_status

        self._task_screen = task_screen
        self._task_screen.set_callback(lambda request: self._task_screen_requests.put(request))
        
        self._search_target_distance = 0.0
        self._scoring = Scoring(lambda score: self._task_screen.show_score(score))
        
        self._task_screen_requests: SimpleQueue[TaskScreenRequest] = SimpleQueue()
        self._controller_actions: SimpleQueue[Action] = SimpleQueue()

        self._delayed_tasks: List[DelayedTask] = list()

        self._logger = EventLogger('scenario')
        
        self._task_distances: List[float] = []
        self._task_distance_index = -1
        self._task_distance = 0.0
        self._task_waiting_for_reply = False
        
        for _ in range(REPETITIONS):
            for dist in DISTANCES:
                self._task_distances.append(dist)
        
        random.shuffle(self._task_distances)
        
        self._car_spawning_location_index = 0

        self._cmd_server = cmd_server
        self._target_type: Optional[str] = None
        self._target_timestamp = 0.0
        
        self._is_running = False
        
    def start(self) -> None:
        self._is_running = True
        
        self._scoring.reset()
        self._next_task()
        
        self._delayed_tasks.append(DelayedTask(1.0, self._spawn_random_target))
        self._delayed_tasks.append(DelayedTask(2.0, self._spawn_next_car))
        
    def tick(self) -> None:
        finished_tasks = [task for task in self._delayed_tasks if task.tick()]
        for task in finished_tasks:
            self._delayed_tasks.remove(task)
            
        while not self._task_screen_requests.empty():
            request = self._task_screen_requests.get()
            if request.type == TaskScreenRequests.target:
                self._scoring.target_noticed()
                self._logger.log('target', 'noticed', f'{self._search_target_distance:.1f}')
                
                self._target_timestamp = 0.0
                self._controller_actions.put(Action(ActionType.REMOVE_TARGETS))
                self._delayed_tasks.append(DelayedTask(0.5, self._spawn_random_target))

            elif request.type == TaskScreenRequests.questionnaire:
                self._scoring.set_task_result(cast(int, request.data))
                
                # we got a response to the questionnaire, lets resume driving
                self._logger.log('evaluation', 'response', request.data)
                self._task_waiting_for_reply = False
                self._controller_actions.put(Action(ActionType.UNFREEZE))

                if self._next_task():
                    self._delayed_tasks.append(DelayedTask(2.0, self._spawn_next_car))
                else:
                    self._clear_tasks()

                    self._delayed_tasks.append(DelayedTask(0.3, self._task_screen.show_message, ['Done!', 'Thank you!']))
                    self._delayed_tasks.append(DelayedTask(0.8, self._task_screen.hide_button))
                    self._delayed_tasks.append(DelayedTask(1.5, self._controller_actions.put, Action(ActionType.STOP_SCENARIO)))

                    self._logger.log('done')
                    self._is_running = False
                
                self._delayed_tasks.append(DelayedTask(0.5, self._task_screen.hide_questionnaire))
                self._delayed_tasks.append(DelayedTask(1.0, self._continue_driving))
            else:
                print(f'SCN: unknown request: {request.type} ({request.data})')
                
        if (self._target_timestamp > 0.0 and time.perf_counter() - self._target_timestamp) > MAX_TARGET_LIFESPAN:
            self._target_timestamp = 0.0
            self._delayed_tasks.append(DelayedTask(0.5, self._spawn_random_target))
            self._controller_actions.put(Action(ActionType.REMOVE_TARGETS))
    
    def get_action(self) -> Optional[Action]:
        if not self._controller_actions.empty():
            result = self._controller_actions.get()
            print(f'SCN: action {result.type} ({result.param})')
            return result
        
    def set_search_target_distance(self, dist: float) -> None:
        self._search_target_distance = dist
        self._scoring.set_target_distance(dist)
        
    def set_nearest_vehicle_behind(self, name: str, distance: float, lane: str, ego_car_speed: float) -> bool:
        if not self._is_running:
            return False
        
        if not self._task_waiting_for_reply:
            if ego_car_speed > MIN_EGOCAR_SPEED_TO_EVALUATE_LINE_CHANGE_SAFETY and distance < self._task_distance:
                self._clear_tasks()
                self._scoring.set_task(distance, lane, ego_car_speed)

                self._task_waiting_for_reply = True
                self._task_screen.show_questionnaire()
                
                self._controller_actions.put(Action(ActionType.REMOVE_CARS))
                self._controller_actions.put(Action(ActionType.FREEZE))
                
                name = '_'.join(name.split('.')[1:])
                self._logger.log('car', 'approached', name, lane, f'{distance:.1f}')
                self._logger.log('evaluation', 'request')
                
                if self._cmd_server:
                    self._cmd_server.send(NetCmd.hide_mirror)

                self._delayed_tasks.append(DelayedTask(0.1, self._stop_driving))
                
                return True
            
        return False
    
    def report_action_result(self, action: Action, has_spawned: bool):
        if action.type == ActionType.DEBUG_TASK_SCREEN:
            if isinstance(action.param, tuple):
                cmd, *args = action.param
                if cmd == 'button':
                    caption = cast(str, args[0])
                    self._task_screen.show_button(caption)
                elif cmd == 'quest':
                    is_visible = cast(bool, args[0])
                    if is_visible:
                        self._task_screen.show_questionnaire()
                    else:
                        self._task_screen.hide_questionnaire()
                elif cmd == 'message':
                    msg = cast(List[str], args)
                    self._task_screen.show_message(msg)

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
        elif action.type == ActionType.START_SCENARIO:
            pass
        elif action.type == ActionType.STOP_SCENARIO:
            self._delayed_tasks.append(DelayedTask(1.0, self._task_screen.hide_button))
    
    # Internal

    def _spawn_random_target(self) -> None:
        target_type = random.choice([x for x in DriverTask.TARGETS])
        while target_type == self._target_type:
            target_type = random.choice([x for x in DriverTask.TARGETS])
            
        self._target_type = target_type

        name = '_'.join(target_type.split('.')[1:])
        self._logger.log('target', 'spawned', name)
        self._scoring.set_target()
        
        self._target_timestamp = time.perf_counter()
        print('\007')

        self._controller_actions.put(Action(ActionType.SPAWN_TARGET, target_type))
        self._delayed_tasks.append(DelayedTask(1.0, self._task_screen.show_message, ['Please find', f'{DriverTask.TARGETS[target_type]}']))
        self._delayed_tasks.append(DelayedTask(3.0, self._task_screen.show_button))
        
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
        print(f'SCN Cancelling {len(self._delayed_tasks)} tasks')
        for task in self._delayed_tasks:
            print(f'SCN     {task}')
            task.cancel()
        self._delayed_tasks.clear()
