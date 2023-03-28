from src.winapi import Window

from typing import Optional, Tuple, List, cast

import copy
import pygame
import carla
import win32gui

try:
    import numpy as np
except ImportError:
    raise RuntimeError('numpy is not installed')

class Mirror:
    MASK_TRANSPARENT_COLOR = (0, 0, 0)
    MIN_BRIGHTNESS = 0.3
    BRIGHTNESS_CHANGE_PER_TICK = 0.05
    BLANK_COLOR = (255, 255, 255)

    def __init__(self,
                 size: List[int],
                 mask_name: Optional[str] = None,
                 world: Optional[carla.World] = None) -> None:
        self.world = world
        self.width = size[0]
        self.height = size[1]
        
        self.enabled = True
        self.brightness = 1.0
        
        # Internal
        
        # to be set in the descendants
        self.camera: Optional[carla.Sensor]
        self._display: pygame.surface.Surface
        self._wnd: Window
        
        self._mask: Optional[pygame.surface.Surface] = None

        if mask_name is not None:
            mask = pygame.image.load(f'images/{mask_name}.png')
            self._mask = pygame.transform.scale(mask, (self.width + 1, self.height + 1))  # black lines may be visible at the edges if we do not expand the image by 1 pixels in each dimension

        self._is_mouse_down: bool = False
        self._mouse_pos: Tuple[int, int] = (0, 0)
        self._window_pos: Tuple[int, int] = (0, 0)
        
        self._brightness = self.brightness
        self._must_scale = False
        
    def draw_image(self, image: Optional[carla.Image]) -> None:
        self._update_dimming()

        if not self.enabled:
            self._display.fill(Mirror.BLANK_COLOR)
        elif image is not None:
            buffer = self._get_image_as_array(image)
            normal_view = buffer.swapaxes(0, 1)
            image_surface = pygame.surfarray.make_surface(normal_view)
            if self._must_scale:
                image_surface = pygame.transform.scale(image_surface, (self.width, self.height))
            self._display.blit(image_surface, (0, 0))

        if self._mask is not None:
            self._display.blit(self._mask, (-1, -1))    # there is a 1-pixel black line on the left and top remained visible if we set the origin to 0,0, thus now it is -1,-1

    def toggle_brightness(self):
        self.brightness = 1.0 + Mirror.MIN_BRIGHTNESS - self.brightness

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

    def _make_display(self,
                     size: Tuple[int, int],
                     location: Tuple[int, int]) -> pygame.surface.Surface:
        display = pygame.display.set_mode(size, pygame.constants.HWSURFACE | pygame.constants.DOUBLEBUF | pygame.constants.NOFRAME)

        self._wnd = Window(pygame.display.get_wm_info()['window'])
        self._wnd.set_location(location[0], location[1])

        if self._mask is not None:
            self._wnd.set_transparent_color(Mirror.MASK_TRANSPARENT_COLOR)
            
        return display
    
    def _make_camera(self,
                    width: int,
                    height: int,
                    fov: float,
                    transform: carla.Transform,
                    vehicle: carla.Vehicle) -> Optional[carla.Sensor]:
        if self.world is None:
            return None
        
        camera_bp = self.world.get_blueprint_library().find('sensor.camera.rgb')
        if camera_bp is None:
            return None
        
        camera_bp.set_attribute('image_size_x', str(width))
        camera_bp.set_attribute('image_size_y', str(height))
        camera_bp.set_attribute('fov', str(fov))
        
        return cast(carla.Sensor, self.world.spawn_actor(
            blueprint = camera_bp,
            transform = transform,
            attach_to = vehicle))

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