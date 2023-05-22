from typing import Optional

import pygame
import carla

from src.settings import Settings, Side
from src.offset import Offset
from src.mirror.base import Mirror


class RectanularMirror(Mirror):
    CAMERAS = {
        'vehicle.lincoln.mkz_2017': Offset(0.7, 0.9, 1.1),
        'vehicle.toyota.prius': Offset(0.7, 0.9, 1.1),
        'vehicle.audi.tt': Offset(0.4, 0.8, 1.1),
        'vehicle.mercedes.coupe_2020': Offset(0.55, 0.8, 1.1),
        'vehicle.dreyevr.egovehicle': Offset(0.68, 0.9, 1.1),
    }
    
    CAMERA_YAW = 22
    
    camera_offset = Offset()    # camera offset, controlled via set_camera_offset
    
    def __init__(self,
                 settings: Settings,
                 world: Optional[carla.World] = None,
                 vehicle: Optional[carla.Vehicle] = None) -> None:

        screen_size = pygame.display.get_desktop_sizes()[0]
        super().__init__(settings.size or [screen_size[0], screen_size[1]], 'fullscreen', None, world) 

        self._display = self._make_display((self.width, self.height))

        cam_y = -RectanularMirror.camera_offset.left if settings.side == Side.RLEFT else RectanularMirror.camera_offset.left
        cam_rot = (180 + RectanularMirror.CAMERA_YAW) if settings.side == Side.RLEFT else (180 - RectanularMirror.CAMERA_YAW)
        transform = carla.Transform(
            carla.Location(x = RectanularMirror.camera_offset.forward, y = cam_y, z = RectanularMirror.camera_offset.up),
            carla.Rotation(yaw = cam_rot)
        )
        self.camera = self._make_camera(480, 320, settings.fov, transform, vehicle) if vehicle is not None else None
        
        self._must_scale = True

    @staticmethod
    def set_camera_offset(vehicle_type: str):
        if vehicle_type in RectanularMirror.CAMERAS:
            RectanularMirror.camera_offset = RectanularMirror.CAMERAS[vehicle_type]
        else:
            print(f'MFS: The camera for {vehicle_type} is not defined')
