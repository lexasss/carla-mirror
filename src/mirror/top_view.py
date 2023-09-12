# Based on a script by:
# Copyright (c) 2021 Computer Vision Center (CVC) at the Universitat Autonoma de Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

from typing import Optional

import carla

from src.common.settings import Settings
from src.mirror.base import Mirror


class TopViewMirror(Mirror):
    CAMERA_YAW = 0
    CAMERA_PITCH = -90   # direct to the ground
    CAMERA_Z = 14         # meters above the ground
    
    def __init__(self,
                 settings: Settings,
                 world: Optional[carla.World] = None,
                 vehicle: Optional[carla.Vehicle] = None) -> None:

        super().__init__(settings.type.value,
                         [480, 320],
                         settings.size,
                         settings.location,
                         mask_name = None,
                         world = world,
                         is_camera = True) 
                
        if not self._settings.is_initialized():
            self._window_pos = (0, 0)
        
        self._display = self._make_display((self.width, self.height))
        
        transform = carla.Transform(
            carla.Location(x = 0, y = 0, z = TopViewMirror.CAMERA_Z),
            carla.Rotation(pitch = TopViewMirror.CAMERA_PITCH, yaw = TopViewMirror.CAMERA_YAW)
        )
        self.camera = self._make_camera(self.width, self.height, settings.fov, transform, vehicle) if vehicle is not None else None

    # Internal
