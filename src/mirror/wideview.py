from typing import Optional

import carla
import pygame

from src.settings import Settings
from src.mirror.base import Mirror

class WideviewMirror(Mirror):
    CAMERAS_Z = {
        'vehicle.lincoln.mkz_2017': 1.8,
        'vehicle.toyota.prius': 1.5,
        'vehicle.audi.tt': 1.5,
        'vehicle.mercedes.coupe_2020': 1.5,
        'vehicle.dreyevr.egovehicle': 1.8,
    }

    CAMERA_PITCH = -6       # slightly downward
    CAMERA_X = 0.5
    
    camera_z = 1.8
    
    def __init__(self,
                 settings: Settings,
                 world: Optional[carla.World] = None,
                 vehicle: Optional[carla.Vehicle] = None) -> None:

        shader = 'zoom_x' if settings.distort else None
        super().__init__(settings.size or [960, 240], 'wideview', 'wideview_mirror', world, shader) 

        if not self._settings.is_initialized():
            screen_size = pygame.display.get_desktop_sizes()[0]
            self._window_pos = (int((screen_size[0] - self.width) / 2), 0)
        
        self._display = self._make_display((self.width, self.height))

        pitch = settings.pitch if settings.pitch is not None else WideviewMirror.CAMERA_PITCH
        transform = carla.Transform(
            carla.Location(x = WideviewMirror.CAMERA_X, z = WideviewMirror.camera_z),
            carla.Rotation(pitch = pitch, yaw = 180)
        )
        self.camera = self._make_camera(self.width, self.height, settings.fov, transform, vehicle) if vehicle is not None else None
                                        # lens_y_size = '0.8',
                                        # lens_kcube = '1000.0',
                                        # lens_k = '1000.5',
                                        # blur_amount = '0.0'

    @staticmethod
    def set_camera_offset(vehicle_type: str):
        if vehicle_type in WideviewMirror.CAMERAS_Z:
            WideviewMirror.camera_z = WideviewMirror.CAMERAS_Z[vehicle_type]
        else:
            print(f'MWV: The camera for {vehicle_type} is not defined')
