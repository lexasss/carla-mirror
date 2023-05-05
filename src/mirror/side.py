# Based on a script by:
# Copyright (c) 2021 Computer Vision Center (CVC) at the Universitat Autonoma de Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

from typing import Optional

import pygame
import carla

from src.settings import Settings, Side
from src.offset import Offset
from src.mirror.base import Mirror


class SideMirror(Mirror):
    CAMERAS = {
        'vehicle.lincoln.mkz_2017': Offset(0.7, 0.9, 1.1),
        'vehicle.toyota.prius': Offset(0.7, 0.9, 1.1),
        'vehicle.audi.tt': Offset(0.4, 0.8, 1.1),
        'vehicle.mercedes.coupe_2020': Offset(0.55, 0.8, 1.1),
    }
    
    CAMERA_YAW = 18
    
    camera_offset = Offset(0.32, 0.10, 1.28)
    
    def __init__(self,
                 settings: Settings,
                 world: Optional[carla.World] = None,
                 vehicle: Optional[carla.Vehicle] = None) -> None:

        super().__init__(settings.size or [480, 320], settings.side.value, f'{settings.side.value}_mirror', world) 
                
        if not self._settings.is_initialized():
            screen_size = pygame.display.get_desktop_sizes()[0]
            self._window_pos = (0 if settings.side == Side.LEFT else screen_size[0] - self.width, screen_size[1] - self.height)
        
        self._display = self._make_display((self.width, self.height))
        
        cam_y, cam_rot = (-SideMirror.camera_offset.left, 180 + SideMirror.CAMERA_YAW) if settings.side == Side.LEFT else (SideMirror.camera_offset.left, 180 - SideMirror.CAMERA_YAW)
        transform = carla.Transform(
            carla.Location(x = SideMirror.camera_offset.forward, y = cam_y, z = SideMirror.camera_offset.up),
            carla.Rotation(yaw = cam_rot)
        )
        self.camera = self._make_camera(self.width, self.height, settings.fov, transform, vehicle) if vehicle is not None else None

    @staticmethod
    def set_camera_offset(vehicle_type: str):
        if vehicle_type in SideMirror.CAMERAS:
            SideMirror.camera_offset = SideMirror.CAMERAS[vehicle_type]
        else:
            print(f'MSD: The camera for {vehicle_type} is not defined')

    # Internal
