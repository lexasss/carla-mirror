from src.winapi import Window
from src.settings import Settings
from src.mirror.settings import MirrorSettings
from src.mirror.opengl_renderer import OpenGLRenderer

from typing import Optional, Tuple, List, cast

# import copy
import pygame
import carla
import win32gui
import win32api

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
                 default_size: List[int],
                 size: Optional[List[int]],
                 type: str,
                 mask_name: Optional[str] = None,
                 world: Optional[carla.World] = None,
                 shader: Optional[str] = None,
                 is_camera: bool = False,
                 screen: Optional[int] = None) -> None:
        self.world = world
        
        self.enabled = True
        self.brightness = 1.0
        self.shader = shader
        self.is_camera = is_camera
        
        # Internal

        self._settings, settings_are_loaded = MirrorSettings.create(type)
        
        if size:
            self.width = size[0]
            self.height = size[1]
        else:
            self.width = self._settings.width if self._settings.width else default_size[0]
            self.height = self._settings.height if self._settings.height else default_size[1]
        
        # to be set in the descendants
        self.camera: Optional[carla.Sensor]
        self._display: pygame.surface.Surface
        self._wnd: Window
        
        # continue initializing
   
        self._display_gl: Optional[OpenGLRenderer] = None

        self._mask: Optional[pygame.surface.Surface] = None

        if mask_name:
            mask = pygame.image.load(f'images/{mask_name}.png')
            self._mask = pygame.transform.scale(mask, (self.width + 1, self.height + 1))  # black lines may be visible at the edges if we do not expand the image by 1 pixels in each dimension

        self._is_mouse_down: bool = False
        self._mouse_pos: Tuple[int, int] = (0, 0)
        
        pos = self._settings.x, self._settings.y
        if screen is not None and not settings_are_loaded:
            monitors = win32api.EnumDisplayMonitors()
            if len(monitors) > screen:
                info = monitors[screen]
                rect = info[2]
                pos = rect[0], rect[1]
             
        self._window_pos: Tuple[int, int] = pos
        
        self._brightness = self.brightness
        self._must_scale = False
        self._offset = (self._settings.offset_x, self._settings.offset_y)
        self._is_topmost = True
        
        self._settings.width = self.width
        self._settings.height = self.height
        MirrorSettings.save(self._settings)
        
    def draw_image(self, image: Optional[carla.Image]) -> None:
        self._update_dimming()

        if not self.enabled:
            self._display.fill(Mirror.BLANK_COLOR)
        elif image:
            buffer = self._get_image_as_array(image)
            normal_view = buffer.swapaxes(0, 1)
            image_surface = pygame.surfarray.make_surface(normal_view)
            if self._must_scale:
                image_surface = pygame.transform.scale(image_surface, (self.width, self.height))
            self._display.blit(image_surface, self._offset)
        else:
            self._display.fill(Mirror.MASK_TRANSPARENT_COLOR)
            
            # draw a matrix of circles, so we can inpect how the view is distorted in the shader
            CELL_SIZE = 50
            row_count = round(self.height / CELL_SIZE)
            col_count = round(self.width / CELL_SIZE)
            
            cell_width = self.width / col_count
            cell_height = self.height / row_count
            for i in range(col_count):
                for j in range(row_count):
                    x = (i + 0.5) * cell_width + self._offset[0]
                    y = (j + 0.5) * cell_height + self._offset[1]
                    pygame.draw.circle(self._display, (255,0,255), (x,y), 10)

        if self._mask:
            self._display.blit(self._mask, (-1, -1))    # there is a 1-pixel black line on the left and top remained visible if we set the origin to 0,0, thus now it is -1,-1

        if self._display_gl:
            texture_data = self._display.get_view('1')
            self._display_gl.render(texture_data)

    def toggle_brightness(self):
        self.brightness = 1.0 + Mirror.MIN_BRIGHTNESS - self.brightness
        
    def on_offset(self, cmd: str) -> None:
        # to be overriden
        pass

    def on_mouse(self, cmd: str) -> None:
        if cmd == 'down' and not self._is_mouse_down:
            self._is_mouse_down = True
            self._mouse_pos = win32gui.GetCursorPos()
            self._window_pos = self._wnd.get_location()
        elif cmd == 'up' and self._is_mouse_down:
            self._is_mouse_down = False
            self._settings.x, self._settings.y = self._wnd.get_location()
            MirrorSettings.save(self._settings)
        elif self._is_mouse_down:
            mouse_x, mouse_y = win32gui.GetCursorPos()
            x = self._window_pos[0] + mouse_x - self._mouse_pos[0]
            y = self._window_pos[1] + mouse_y - self._mouse_pos[1]
            self._wnd.set_location(x, y, self._is_topmost)
        elif cmd.startswith('move'):
            if self._display_gl:
                a = [float(x) for x in cmd[4:].split(',')]
                self._display_gl.mouse = (self.width - a[0]), a[1]
        elif cmd == 'scroll_up':
            if self._display_gl:
                self._display_gl.zoomIn()
        elif cmd == 'scroll_down':
            if self._display_gl:
                self._display_gl.zoom_out()
                

    # Internal

    def _make_display(self, size: Tuple[int, int]) -> pygame.surface.Surface:
        if self.shader:
            settings = Settings()
            self._display_gl = OpenGLRenderer(
                size,
                self.shader,
                self.world is None,
                settings.is_shader_control_by_mouse,
                settings.distortion_circle_radius)
            display = self._display_gl.screen
        else:
            display = pygame.display.set_mode(size, pygame.constants.DOUBLEBUF | pygame.constants.NOFRAME)

        icon = pygame.image.load('images/icon.png')
        pygame.display.set_icon(icon)

        self._wnd = Window(size, pygame.display.get_wm_info()['window'])
        self._wnd.set_location(self._window_pos[0], self._window_pos[1], self._is_topmost)

        if self._mask:
            self._wnd.set_transparent_color(Mirror.MASK_TRANSPARENT_COLOR)
            
        display.fill(Mirror.MASK_TRANSPARENT_COLOR)
        
        return display
    
    def _make_camera(self,
                    width: int,
                    height: int,
                    fov: float,
                    transform: carla.Transform,
                    vehicle: carla.Vehicle,
                    **kwargs: str) -> Optional[carla.Sensor]:
        if self.world is None:
            return None
        
        camera_bp = self.world.get_blueprint_library().find('sensor.camera.rgb')
        if camera_bp is None:
            return None
        
        camera_bp.set_attribute('image_size_x', str(width))
        camera_bp.set_attribute('image_size_y', str(height))
        camera_bp.set_attribute('fov', str(fov))
        
        for key in kwargs:
            print(f'CAM: {key} = {kwargs[key]}')
            camera_bp.set_attribute(key, kwargs[key])
        
        return cast(carla.Sensor, self.world.spawn_actor(
            blueprint = camera_bp,
            transform = transform,
            attach_to = vehicle))

    def _get_image_as_array(self, image: carla.Image) -> 'np.ArrayLike[np.uint8]':
        array_one_dim = np.frombuffer(image.raw_data, dtype = np.uint8)
        array = np.reshape(array_one_dim, (image.height, image.width, 4))
        
        # BGR -> RGB (last dimension: takes 3 bytes in reversed order)
        if self.is_camera:
            array = array[:, :, 2::-1]
        else:
            # NOTICE we reverse bytes on the X axis (second dimension): this way we get a mirrored view!
            array = array[:, ::-1, 2::-1]
        
        if self._brightness < 1:
            array = array * self._brightness
        
        return array
        
        # make the array writeable doing a deep copy
        #return copy.deepcopy(array)
        
    def _update_dimming(self):
        if self.brightness < self._brightness:
            self._brightness = max(self._brightness - Mirror.BRIGHTNESS_CHANGE_PER_TICK, self.brightness)
        elif self.brightness > self._brightness:
            self._brightness = min(self._brightness + Mirror.BRIGHTNESS_CHANGE_PER_TICK, self.brightness)
