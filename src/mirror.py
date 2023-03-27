# Based on a script by:
# Copyright (c) 2021 Computer Vision Center (CVC) at the Universitat Autonoma de Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

from src.winapi import Window

from typing import Optional, Tuple, cast

import copy
import pygame
import carla
import win32gui

try:
    import numpy as np
except ImportError:
    raise RuntimeError('numpy is not installed')

from src.settings import Settings, Side
from src.offset import Offset


class Mirror:
    CAMERAS = {
        'vehicle.lincoln.mkz_2017': Offset(0.7, 0.9, 1.1),
        'vehicle.toyota.prius': Offset(0.7, 0.9, 1.1),
        'vehicle.audi.tt': Offset(0.4, 0.8, 1.1),
        'vehicle.mercedes.coupe_2020': Offset(0.55, 0.8, 1.1),
    }
    
    CAMERA_YAW = 18
    MASK_TRANSPARENT_COLOR = (0, 0, 0)
    BLANK_COLOR = (255, 255, 255)
    MIN_BRIGHTNESS = 0.3
    BRIGHTNESS_CHANGE_PER_TICK = 0.05
    
    camera_offset = Offset(0.32, 0.10, 1.28)
    
    def __init__(self,
                 settings: Settings,
                 world: Optional[carla.World] = None,
                 vehicle: Optional[carla.Vehicle] = None) -> None:
        self.world = world
        self.display = self.make_display(settings.width, settings.height, settings.side)
    
        mask = pygame.image.load(f'images/{settings.side.value}_mirror.png')
        self.mask = pygame.transform.scale(mask, (settings.width + 1, settings.height + 1))  # black lines may be visible at the edges if we do not expand the image by 1 pixels in each dimension
        self.camera = self.make_camera(settings.width, settings.height, settings.fov, settings.side, vehicle) if vehicle is not None else None

        self.enabled = True
        self.brightness = 1.0
        
        # Internal
        
        self._is_mouse_down: bool = False
        self._mouse_pos: Tuple[int, int] = (0, 0)
        self._window_pos: Tuple[int, int] = (0, 0)
        
        self._brightness = self.brightness

    @staticmethod
    def set_camera_offset(vehicle_type: str):
        if vehicle_type in Mirror.CAMERAS:
            Mirror.camera_offset = Mirror.CAMERAS[vehicle_type]
        else:
            print(f'The camera for {vehicle_type} is not defined')
    
    def make_display(self,
                     width: int,
                     height: int,
                     side: Side) -> pygame.surface.Surface:
        display = pygame.display.set_mode((width, height), pygame.constants.HWSURFACE | pygame.constants.DOUBLEBUF | pygame.constants.NOFRAME)
        screen_size = pygame.display.get_desktop_sizes()[0]

        win_x = 0 if side == Side.LEFT else screen_size[0] - width
        win_y = screen_size[1] - height

        self._wnd = Window(pygame.display.get_wm_info()['window'])
        self._wnd.set_transparent_color(Mirror.MASK_TRANSPARENT_COLOR)
        self._wnd.set_location(win_x, win_y)
            
        return display

    def make_font(self,
                  name: str = 'ubuntumono',
                  size: int = 14) -> pygame.font.Font:
        fonts = [x for x in pygame.font.get_fonts()]
        font = name if name in fonts else fonts[0]
        font = pygame.font.match_font(font)
        return pygame.font.Font(font, size)

    def make_camera(self,
                    width: int,
                    height: int,
                    fov: float,
                    side: Side,
                    vehicle: carla.Vehicle) -> Optional[carla.Sensor]:
        if self.world is None:
            return None
        
        camera_bp = self.world.get_blueprint_library().find('sensor.camera.rgb')
        if camera_bp is None:
            return None
        
        camera_bp.set_attribute('image_size_x', str(width))
        camera_bp.set_attribute('image_size_y', str(height))
        camera_bp.set_attribute('fov', str(fov))
        
        cam_y, cam_rot = (-Mirror.camera_offset.left, 180 + Mirror.CAMERA_YAW) if side == Side.LEFT else (Mirror.camera_offset.left, 180 - Mirror.CAMERA_YAW)
        return cast(carla.Sensor, self.world.spawn_actor(
            blueprint = camera_bp,
            transform = carla.Transform(
                carla.Location(x = Mirror.camera_offset.forward, y = cam_y, z = Mirror.camera_offset.up),
                carla.Rotation(yaw = cam_rot)
            ),
            attach_to = vehicle))

    def toggle_brightness(self):
        self.brightness = 1.0 + Mirror.MIN_BRIGHTNESS - self.brightness
        
    def draw_image(self,
                   image: carla.Image,
                   blend: bool = False) -> None:
        if not self.enabled:
            self.display.fill(Mirror.BLANK_COLOR)
            return
        
        self._update_dimming()
        
        buffer = self._get_image_as_array(image)
        normal_view = buffer.swapaxes(0, 1)

        image_surface = pygame.surfarray.make_surface(normal_view)
        if blend:
            image_surface.set_alpha(100)
        self.display.blit(image_surface, (0, 0))
        
    def draw_mask(self) -> None:
        self.display.blit(self.mask, (-1, -1))    # there is a 1-pixel black line on the left and top remained visible if we set the origin to 0,0, thus now it is -1,-1

    def on_mouse(self, cmd: Optional[str]) -> None:
        if cmd == 'down' and not self._is_mouse_down:
            self._is_mouse_down = True
            self._mouse_pos = win32gui.GetCursorPos()
            self._window_pos = self._wnd.get_location()
        elif cmd == 'up' and self._is_mouse_down:
            self._is_mouse_down = False
        elif self._is_mouse_down:
            mouse_x, mouse_y = win32gui.GetCursorPos()
            x = self._window_pos[0] + mouse_x - self._mouse_pos[0]
            y = self._window_pos[1] + mouse_y - self._mouse_pos[1]
            self._wnd.set_location(x, y)

    # Internal
    
    def _get_image_as_array(self, image: carla.Image) -> 'np.ArrayLike[np.uint8]':
        array_one_dim = np.frombuffer(image.raw_data, dtype = np.uint8)
        array = np.reshape(array_one_dim, (image.height, image.width, 4))
        
        # BGR -> RGB (last dimension: takes 3 bytes in reversed order)
        # NOTICE we reverse bytes on the X axis (second dimension): this way we get a mirrored view!
        array = array[:, ::-1, 2::-1] * self._brightness
        
        # make the array writeable doing a deep copy
        return copy.deepcopy(array)

    def _update_dimming(self):
        if self.brightness < self._brightness:
            self._brightness = max(self._brightness - Mirror.BRIGHTNESS_CHANGE_PER_TICK, self.brightness)
        elif self.brightness > self._brightness:
            self._brightness = min(self._brightness + Mirror.BRIGHTNESS_CHANGE_PER_TICK, self.brightness)