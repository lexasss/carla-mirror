from typing import Optional, Tuple, List

from src.exp.scenario import DISTANCES
from src.common.logging import TrafficLogger
from src.common.lane import Lane

class ZONE_EDGE:
    far = DISTANCES[2] - 5
    mid = DISTANCES[1] - 5

class TrafficState:
    def __init__(self) -> None:
        self.reset()
        self.ego_car_lane_props: Optional[Tuple[float, float]]
        
        self._logger = TrafficLogger()
        self._logger.log(
            'ec_pos_x',
            'ec_pos_y',
            'same_far',
            'same_mid',
            'same_close',
            'next_far',
            'next_mid',
            'next_close'
        )
        
    def reset(self) -> None:
        self._same_lane_far = 0
        self._same_lane_mid = 0
        self._same_lane_close = 0
        self._next_lane_far = 0
        self._next_lane_mid = 0
        self._next_lane_close = 0
        
    def update(self, list: List[Tuple[float, Lane]]) -> None:
        for distance, lane in list:
            if lane == Lane.SAME:
                if distance > ZONE_EDGE.far:
                    self._same_lane_far = 1
                elif distance > ZONE_EDGE.mid:
                    self._same_lane_mid = 1
                else:
                    self._same_lane_close = 1
            else:
                if distance > ZONE_EDGE.far:
                    self._next_lane_far = 1
                elif distance > ZONE_EDGE.mid:
                    self._next_lane_mid = 1
                else:
                    self._next_lane_close = 1
        
    def log(self) -> None:
        ec_pos_x, ec_pos_y = self.ego_car_lane_props if self.ego_car_lane_props else (0.0, 0.0) 
        self._logger.log(
            f'{ec_pos_x:.3f}',
            f'{ec_pos_y:.2f}',
            self._same_lane_far,
            self._same_lane_mid,
            self._same_lane_close,
            self._next_lane_far,
            self._next_lane_mid,
            self._next_lane_close
        )
        