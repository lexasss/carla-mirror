from typing import Optional

import pygame
import carla

from src.settings import Settings
from src.mirror.base import Mirror


class WideviewMirror(Mirror):
    CAMERAS_Z = {
        'vehicle.lincoln.mkz_2017': 1.5,
        'vehicle.toyota.prius': 1.5,
        'vehicle.audi.tt': 1.5,
        'vehicle.mercedes.coupe_2020': 1.5,
    }

    CAMERA_PITCH = -10
    
    camera_z = 1.8
    
    def __init__(self,
                 settings: Settings,
                 world: Optional[carla.World] = None,
                 vehicle: Optional[carla.Vehicle] = None) -> None:

        super().__init__(settings.size or [960, 240], 'wideview_mirror', world) 

        screen_size = pygame.display.get_desktop_sizes()[0]
        win_x = int((screen_size[0] - self.width) / 2)
        win_y = 0
        self._display = self._make_display((self.width, self.height), (win_x, win_y))

        transform = carla.Transform(
            carla.Location(z = WideviewMirror.camera_z),
            carla.Rotation(pitch = WideviewMirror.CAMERA_PITCH, yaw = 180)
        )
        self.camera = self._make_camera(self.width, self.height, settings.fov, transform, vehicle) if vehicle is not None else None

    @staticmethod
    def set_camera_offset(vehicle_type: str):
        if vehicle_type in WideviewMirror.CAMERAS_Z:
            WideviewMirror.camera_offset = WideviewMirror.CAMERAS_Z[vehicle_type]
        else:
            print(f'The camera for {vehicle_type} is not defined')
