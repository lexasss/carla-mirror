# Based on a script by:
# Copyright (c) 2021 Computer Vision Center (CVC) at the Universitat Autonoma de Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

from typing import Optional

import pygame
import carla

from src.settings import Settings, MirrorType
from src.offset import Offset
from src.mirror.base import Mirror


class SideMirror(Mirror):
    CAMERA = {
        'vehicle.lincoln.mkz_2017': Offset(0.7, 0.9, 1.1),
        'vehicle.toyota.prius': Offset(0.7, 0.9, 1.1),
        'vehicle.audi.tt': Offset(0.4, 0.8, 1.1),
        'vehicle.mercedes.coupe_2020': Offset(0.55, 0.8, 1.1),
        'vehicle.dreyevr.egovehicle': Offset(0.7, 0.9, 1.1),
    }
    
    CAMERA_YAW_TOWARD_CAR = 2
    
    camera_offset = Offset(0.32, 0.10, 1.28)
    
    def __init__(self,
                 settings: Settings,
                 world: Optional[carla.World] = None,
                 vehicle: Optional[carla.Vehicle] = None) -> None:

        shader = 'zoom_out' if settings.distort else None
        super().__init__([480, 320],
                         size = settings.size,
                         type = settings.type.value,
                         mask_name = f'{settings.type.value}_mirror',
                         world = world,
                         shader = shader) 
                
        if not self._settings.is_initialized():
            screen_size = pygame.display.get_desktop_sizes()[0]
            self._window_pos = (0 if settings.type == MirrorType.LEFT else screen_size[0] - self.width, screen_size[1] - self.height)
        
        self._display = self._make_display((self.width, self.height))
        if self._display_gl:
            self._display_gl.inject_uniforms(reversed = settings.type == MirrorType.RIGHT)
        
        cam_y = 0
        cam_rot = 180
        if settings.type == MirrorType.LEFT:
            cam_y = -SideMirror.camera_offset.left
            cam_rot = 180 + (settings.fov / 2 - SideMirror.CAMERA_YAW_TOWARD_CAR)
        else:
            cam_y = SideMirror.camera_offset.left
            cam_rot = 180 - (settings.fov / 2 + SideMirror.CAMERA_YAW_TOWARD_CAR)
            
        transform = carla.Transform(
            carla.Location(x = SideMirror.camera_offset.forward, y = cam_y, z = SideMirror.camera_offset.up),
            carla.Rotation(yaw = cam_rot)
        )
        self.camera = self._make_camera(self.width, self.height, settings.fov, transform, vehicle) if vehicle is not None else None

    @staticmethod
    def set_camera_offset(vehicle_type: str):
        if vehicle_type in SideMirror.CAMERA:
            SideMirror.camera_offset = SideMirror.CAMERA[vehicle_type]
        else:
            print(f'MSD: The camera for {vehicle_type} is not defined')

    # Internal
