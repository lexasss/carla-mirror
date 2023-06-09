from typing import Optional

import carla
import pygame

from src.settings import Settings
from src.mirror.base import Mirror

class WideviewMirror(Mirror):
    CAMERA_Z = {
        'vehicle.lincoln.mkz_2017': 1.8,
        'vehicle.toyota.prius': 1.5,
        'vehicle.audi.tt': 1.5,
        'vehicle.mercedes.coupe_2020': 1.5,
        'vehicle.dreyevr.egovehicle': 1.8,
    }

    CAMERA_PITCH_K = -20        # value of fov per one degree downward: for example, if fov=120 and CAMERA_PITCH_K=-20, then the camera pitch is 120/-20 = -6
    CAMERA_X = 0.5              # offset forward
    
    camera_z = 1.8      # one of value from CAMERAS_Z, set via set_camera_offset
    
    def __init__(self,
                 settings: Settings,
                 world: Optional[carla.World] = None,
                 vehicle: Optional[carla.Vehicle] = None) -> None:

        shader = 'zoom_in' if settings.distortion is not None else None
        super().__init__('wideview',
                         [960, 240],
                         settings.size,
                         settings.location,
                         mask_name = 'wideview_mirror',
                         world = world,
                         shader = shader)

        if not self._settings.is_initialized():
            screen_size = pygame.display.get_desktop_sizes()[0]
            self._window_pos = (int((screen_size[0] - self.width) / 2), 0)
        
        self._display = self._make_display((self.width, self.height))

        pitch = settings.pitch if settings.pitch is not None else settings.fov / WideviewMirror.CAMERA_PITCH_K
        transform = carla.Transform(
            carla.Location(x = WideviewMirror.CAMERA_X, z = WideviewMirror.camera_z),
            carla.Rotation(pitch = pitch, yaw = 180)
        )
        self.camera = self._make_camera(self.width, self.height, settings.fov, transform, vehicle) if vehicle is not None else None

    @staticmethod
    def set_camera_offset(vehicle_type: str):
        if vehicle_type in WideviewMirror.CAMERA_Z:
            WideviewMirror.camera_z = WideviewMirror.CAMERA_Z[vehicle_type]
        else:
            print(f'MWV: The camera for {vehicle_type} is not defined')
