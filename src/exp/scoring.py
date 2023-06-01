import sys
from typing import Callable

# from src.exp.task_screen import TaskResponse
from src.carla.lane import Lane

MAX_SCORE_TARGET: float = 100
MAX_SCORE_TASK: float = 100

PENALTY = 10

class Scoring:
    def __init__(self, cb: Callable[[int], None]) -> None:
        self._cb = cb
        
        self._score = 0
        self._score_for_target = MAX_SCORE_TARGET
        self._score_for_task = MAX_SCORE_TASK
        
        self._task_correct_answer = 0
        
        self._target_distance = sys.float_info.max
        self._is_approaching = False
        
    def reset(self) -> None:
        self._score = 0
        self._cb(self._score)
        
    def set_target(self) -> None:
        self._score_for_target = MAX_SCORE_TARGET
        self._target_distance = sys.float_info.max
        self._is_approaching = False

    def set_target_distance(self, dist: float) -> None:
        if dist == 0:
            return
        
        is_approaching = dist < self._target_distance
        
        if dist < 20 and not is_approaching and self._is_approaching:
            # missed the target
            self._score_for_target = self._score_for_target / 2
            print(F'Missed the target')
            
        self._target_distance = dist
        self._is_approaching = is_approaching

    def target_noticed(self) -> None:
        if self._target_distance < 100:
            # probably, target will be visible no more that from this far
            self._score += int(self._score_for_target)
        else:
            # this is a fake notice: the target was too far to notice
            self._score -= PENALTY
            
        self._cb(self._score)
    
    def set_task(self, distance: float, lane: str, ego_car_speed: float) -> None:
        self._score_for_task = MAX_SCORE_TASK
        
        if lane == Lane.SAME:
            self._score_for_task *= 0.8
            if distance < 10:
                self._task_correct_answer = 1
            else:
                self._task_correct_answer = 0
        else:
            if distance < 10:
                self._task_correct_answer = 3
            elif distance < 20:
                self._task_correct_answer = 2
            else:
                self._task_correct_answer = 0
            
        if distance < 10:
            self._score_for_task *= 0.8 * 0.8
        elif distance < 20:
            self._score_for_task *= 0.8
        
    def set_task_result(self, response: int) -> None:
        diff = abs(response - self._task_correct_answer)

        if diff == 0:
            self._score += int(self._score_for_task)
        elif diff == 1:
            self._score += int(self._score_for_task / 2)
        elif diff == 2:
            # no points earned, as the response is not correct
            pass
        elif diff >= 3:
            # apply a penalty, as the response is completely wrong
            self._score -= PENALTY
            
        self._cb(self._score)
        