from typing import Optional

import pygame
import carla

from src.common.settings import Settings, MirrorType
from src.common.offset import Offset
from src.mirror.base import Mirror
from src.mirror.settings import MirrorSettings


class RectangularMirror(Mirror):
    CAMERA = {
        'vehicle.lincoln.mkz_2017': Offset(0.67, 0.9, 1.1),
        'vehicle.toyota.prius': Offset(0.7, 0.9, 1.1),
        'vehicle.audi.tt': Offset(0.4, 0.8, 1.1),
        'vehicle.mercedes.coupe_2020': Offset(0.55, 0.8, 1.1),
        'vehicle.dreyevr.egovehicle': Offset(0.68, 0.9, 1.1),
    }
    
    REAR_VIEW_CAMERA_Z = {
        'vehicle.lincoln.mkz_2017': 1.3,
        'vehicle.toyota.prius': 1.3,
        'vehicle.audi.tt': 1.3,
        'vehicle.mercedes.coupe_2020': 1.3,
        'vehicle.dreyevr.egovehicle': 1.65,
    }

    REAR_VIEW_CAMERA_X = 0.3              # offset forward
    
    CAMERA_PITCH_K = -20        # value of fov per one degree downward: for example, if fov=120 and CAMERA_PITCH_K=-20, then the camera pitch is 120/-20 = -6
    CAMERA_YAW_TOWARD_CAR = 2
    
    camera_offset = Offset()    # camera offset, controlled via set_camera_offset
    rear_view_camera_elevation = 0
    
    def __init__(self,
                 settings: Settings,
                 world: Optional[carla.World] = None,
                 vehicle: Optional[carla.Vehicle] = None) -> None:

        screen_sizes = pygame.display.get_desktop_sizes()
        screen_size = screen_sizes[0]
        if settings.use_smart_display:
            mirror_screen = Mirror.get_best_fit_screen_rect(settings.type.value)
            screen_size = mirror_screen[2], mirror_screen[3]
        else:
            if settings.screen < len(screen_sizes):
                screen_size = screen_sizes[settings.screen]
        
        if settings.distortion is not None:
            shader = 'zoom_in'
        else:
            shader = None
            
        super().__init__(settings.type.value,
                         [screen_size[0], screen_size[1]],
                         settings.size,
                         settings.location,
                         settings.offset,
                         mask_name = None,
                         world = world,
                         shader = shader,
                         screen = settings.screen,
                         use_smart_display = settings.use_smart_display) 

        if settings.is_fullscreen or not settings.size:
            self._is_topmost = False
            display_size = screen_size
        else:
            display_size = (settings.size[0], settings.size[1])

        self._display = self._make_display(display_size)
        if self._display_gl:
            self._display_gl.inject_uniforms(reversed = settings.type == MirrorType.RRIGHT)

        cam_x = RectangularMirror.camera_offset.forward
        cam_y = 0
        cam_z = RectangularMirror.camera_offset.up
        cam_yaw = 180
        cam_pitch = settings.pitch if settings.pitch is not None else settings.fov / RectangularMirror.CAMERA_PITCH_K
        if settings.type == MirrorType.RLEFT:
            cam_y = -RectangularMirror.camera_offset.left
            if settings.yaw is not None:
                cam_yaw = settings.yaw
            else:
                cam_yaw = 180 + (settings.fov / 2 - RectangularMirror.CAMERA_YAW_TOWARD_CAR)
        elif settings.type == MirrorType.RRIGHT:
            cam_y = RectangularMirror.camera_offset.left
            if settings.yaw is not None:
                cam_yaw = settings.yaw
            else:
                cam_yaw = 180 - (settings.fov / 2 - RectangularMirror.CAMERA_YAW_TOWARD_CAR)
        elif settings.type == MirrorType.RREAR:
            cam_x = RectangularMirror.REAR_VIEW_CAMERA_X
            cam_z = RectangularMirror.rear_view_camera_elevation
            cam_pitch = -8
            if settings.yaw is not None:
                cam_yaw = settings.yaw
        
        transform = carla.Transform(
            carla.Location(cam_x, cam_y, cam_z),
            carla.Rotation(yaw = cam_yaw, pitch = cam_pitch)
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
        if vehicle_type in RectangularMirror.CAMERA:
            RectangularMirror.camera_offset = RectangularMirror.CAMERA[vehicle_type]
        else:
            print(f'MFS: The camera for {vehicle_type} is not defined')

        if vehicle_type in RectangularMirror.REAR_VIEW_CAMERA_Z:
            RectangularMirror.rear_view_camera_elevation = RectangularMirror.REAR_VIEW_CAMERA_Z[vehicle_type]
        else:
            print(f'MFS: The camera for {vehicle_type} is not defined')