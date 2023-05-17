from typing import Optional

from src.carla.lane import Lane
from src.exp.logging import TrafficLogger

class ZONE_EDGE:
    far = 20
    mid = 10

class TrafficState:
    def __init__(self) -> None:
        self.reset()
        self._logger = TrafficLogger()
        
    def reset(self) -> None:
        self.same_lane_far = 0
        self.same_lane_mid = 0
        self.same_lane_close = 0
        self.next_lane_far = 0
        self.next_lane_mid = 0
        self.next_lane_close = 0
        
    def update(self, distance: float, lane: Optional[str]) -> None:
        if lane == Lane.SAME:
            if distance > ZONE_EDGE.far:
                self.same_lane_far = 1
            elif distance > ZONE_EDGE.mid:
                self.same_lane_mid = 1
            else:
                self.same_lane_close = 1
        else:
            if distance > ZONE_EDGE.far:
                self.next_lane_far = 1
            elif distance > ZONE_EDGE.mid:
                self.next_lane_mid = 1
            else:
                self.next_lane_close = 1
        
    def log(self) -> None:
        self._logger.log(
            self.same_lane_far,
            self.same_lane_mid,
            self.same_lane_close,
            self.next_lane_far,
            self.next_lane_mid,
            self.next_lane_close
        )
        