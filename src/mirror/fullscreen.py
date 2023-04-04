from typing import Optional

import pygame
import carla

from src.settings import Settings, Side
from src.offset import Offset
from src.mirror.base import Mirror


class FullscreenMirror(Mirror):
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

        screen_size = pygame.display.get_desktop_sizes()[0]
        super().__init__(settings.size or [screen_size[0], screen_size[1]], 'fullscreen', None, world) 

        self._display = self._make_display((self.width, self.height))

        cam_y, cam_rot = (-FullscreenMirror.camera_offset.left, 180 + FullscreenMirror.CAMERA_YAW) if settings.side == Side.LEFT else (FullscreenMirror.camera_offset.left, 180 - FullscreenMirror.CAMERA_YAW)
        transform = carla.Transform(
            carla.Location(x = FullscreenMirror.camera_offset.forward, y = cam_y, z = FullscreenMirror.camera_offset.up),
            carla.Rotation(yaw = cam_rot)
        )
        self.camera = self._make_camera(480, 320, settings.fov, transform, vehicle) if vehicle is not None else None
        
        self._must_scale = True

    @staticmethod
    def set_camera_offset(vehicle_type: str):
        if vehicle_type in FullscreenMirror.CAMERAS:
            FullscreenMirror.camera_offset = FullscreenMirror.CAMERAS[vehicle_type]
        else:
            print(f'The camera for {vehicle_type} is not defined')
