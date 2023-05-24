from typing import Optional

import pygame
import carla

from src.settings import Settings, Side
from src.offset import Offset
from src.mirror.base import Mirror
from src.mirror.wideview import WideviewMirror
from src.mirror.settings import MirrorSettings


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
    rear_view_camera_elevation = 0
    
    def __init__(self,
                 settings: Settings,
                 world: Optional[carla.World] = None,
                 vehicle: Optional[carla.Vehicle] = None) -> None:

        screen_size = pygame.display.get_desktop_sizes()[0]
        super().__init__([screen_size[0], screen_size[1]],
                         size = settings.size,
                         side = settings.side.value,
                         mask_name = None,
                         world = world) 

        self._is_topmost = False

        self._display = self._make_display(screen_size)

        cam_x = RectanularMirror.camera_offset.forward
        cam_y = 0
        cam_z = RectanularMirror.camera_offset.up
        cam_rot = 180
        if settings.side == Side.RLEFT:
            cam_y = -RectanularMirror.camera_offset.left
            cam_rot = 180 + RectanularMirror.CAMERA_YAW
        elif settings.side == Side.RRIGHT:
            cam_y = RectanularMirror.camera_offset.left
            cam_rot = 180 - RectanularMirror.CAMERA_YAW
        elif settings.side == Side.RREAR:
            cam_x = WideviewMirror.CAMERA_X
            cam_z = RectanularMirror.rear_view_camera_elevation
            
        transform = carla.Transform(
            carla.Location(cam_x, cam_y, cam_z),
            carla.Rotation(yaw = cam_rot)
        )
        self.camera = self._make_camera(self.width, self.height, settings.fov, transform, vehicle) if vehicle is not None else None
        
        self._must_scale = False
        
    def on_offset(self, cmd: str) -> None:
        for c in cmd:
            if c == 'l':
                self._offset = (self._offset[0] - 10, self._offset[1])
            elif c == 'r':
                self._offset = (self._offset[0] + 10, self._offset[1])
            elif c == 'u':
                self._offset = (self._offset[0], self._offset[1] - 10)
            elif c == 'd':
                self._offset = (self._offset[0], self._offset[1] + 10)
                
        self._settings.offset_x = self._offset[0]
        self._settings.offset_y = self._offset[1]
        MirrorSettings.save(self._settings)
        
        self._display.fill(Mirror.MASK_TRANSPARENT_COLOR)

    @staticmethod
    def set_camera_offset(vehicle_type: str):
        if vehicle_type in RectanularMirror.CAMERAS:
            RectanularMirror.camera_offset = RectanularMirror.CAMERAS[vehicle_type]
        else:
            print(f'MFS: The camera for {vehicle_type} is not defined')

        if vehicle_type in WideviewMirror.CAMERAS_Z:
            RectanularMirror.rear_view_camera_elevation = WideviewMirror.CAMERAS_Z[vehicle_type]
        else:
            print(f'MFS: The camera for {vehicle_type} is not defined')