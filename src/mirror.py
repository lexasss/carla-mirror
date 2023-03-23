#!/usr/bin/env python
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


class Mirror:
    def __init__(self,
                 settings: Settings,
                 world: Optional[carla.World] = None,
                 vehicle: Optional[carla.Vehicle] = None) -> None:
        self.world = world
        self.display = self.make_display(settings.width, settings.height, settings.side)
    
        mask = pygame.image.load(f'images/{settings.side.value}_mirror.png')
        self.mask = pygame.transform.scale(mask, (settings.width + 1, settings.height + 1))  # black lines may be visible at the edges if we do not expand the image by 1 pixels in each dimension
        self.camera = self.make_camera(settings.width, settings.height, settings.fov, settings.side, vehicle) if vehicle is not None else None

        self._is_mouse_down: bool = False
        self._mouse_pos: Tuple[int, int] = (0, 0)
        self._window_pos: Tuple[int, int] = (0, 0)

    
    def make_display(self,
                     width: int,
                     height: int,
                     side: Side) -> pygame.surface.Surface:
        display = pygame.display.set_mode((width, height), pygame.constants.HWSURFACE | pygame.constants.DOUBLEBUF | pygame.constants.NOFRAME)
        screen_size = pygame.display.get_desktop_sizes()[0]

        win_x = 0 if side == Side.LEFT else screen_size[0] - width
        win_y = screen_size[1] - height

        self._wnd = Window(pygame.display.get_wm_info()['window'])
        self._wnd.set_transparent_color((0, 0, 0))
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
        
        CAMERA_OFFSET_SIDE = 0.9
        CAMERA_YAW = 18
        
        camera_bp = self.world.get_blueprint_library().find('sensor.camera.rgb')
        if camera_bp is None:
            return None
        
        camera_bp.set_attribute('image_size_x', str(width))
        camera_bp.set_attribute('image_size_y', str(height))
        camera_bp.set_attribute('fov', str(fov))
        
        cam_y, cam_rot = (-CAMERA_OFFSET_SIDE, 180 + CAMERA_YAW) if side == Side.LEFT else (CAMERA_OFFSET_SIDE, 180 - CAMERA_YAW)
        return cast(carla.Sensor, self.world.spawn_actor(
            blueprint = camera_bp,
            transform = carla.Transform(
                carla.Location(x = 0.7, y = cam_y, z = 1.1),
                carla.Rotation(yaw = cam_rot)
            ),
            attach_to = vehicle))

    def draw_image(self,
                   image: carla.Image,
                   blend: bool = False) -> None:
        buffer = get_image_as_array(image)
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

def get_image_as_array(image: carla.Image) -> 'np.ArrayLike[np.uint8]':
    array_one_dim = np.frombuffer(image.raw_data, dtype = np.uint8)
    array = np.reshape(array_one_dim, (image.height, image.width, 4))
    
    # BGR -> RGB (last dimension: take 3 bytes in reversed order)
    # NOTICE we reverse bytes on the X axis: this way we get a mirrored view!
    array = array[:, ::-1, 2::-1]
    
    # make the array writeable doing a deep copy
    return copy.deepcopy(array)
