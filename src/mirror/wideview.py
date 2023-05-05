from typing import Optional #, Tuple, Callable

import carla
import pygame
# import math
# import numpy as np
# import scipy.ndimage as scimg   # pyright: ignore[reportMissingModuleSource]

from src.settings import Settings
from src.mirror.base import Mirror

# try:
#     from skimage.transform import PiecewiseAffineTransform, warp
# except ImportError:
#     raise RuntimeError('skimage is not installed')


class WideviewMirror(Mirror):
    CAMERAS_Z = {
        'vehicle.lincoln.mkz_2017': 1.8,
        'vehicle.toyota.prius': 1.5,
        'vehicle.audi.tt': 1.5,
        'vehicle.mercedes.coupe_2020': 1.5,
    }

    CAMERA_PITCH = -6       # slightly downward
    CAMERA_X = 0.5
    
    camera_z = 1.8
    
    def __init__(self,
                 settings: Settings,
                 world: Optional[carla.World] = None,
                 vehicle: Optional[carla.Vehicle] = None) -> None:

        super().__init__(settings.size or [960, 240], 'wideview', 'wideview_mirror', world, 'zoom_x') 

        if not self._settings.is_initialized():
            screen_size = pygame.display.get_desktop_sizes()[0]
            self._window_pos = (int((screen_size[0] - self.width) / 2), 0)
        
        self._display = self._make_display((self.width, self.height))

        transform = carla.Transform(
            carla.Location(x = WideviewMirror.CAMERA_X, z = WideviewMirror.camera_z),
            carla.Rotation(pitch = WideviewMirror.CAMERA_PITCH, yaw = 180)
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

    # def _get_image_as_array(self, image: carla.Image) -> 'np.ArrayLike[np.uint8]':
    #     buffer = super()._get_image_as_array(image)
    #     if not WideviewMirror.APPLY_DISTORTION:
    #         return buffer

        # assert buffer.shape is not None
        # width = float(buffer.shape[0])
        # widthD2 = width / 2
        # piD4 = math.pi / 4

        # nrows, ncols, _ = buffer.shape
        # src_cols = np.linspace(0, ncols, 20)
        # src_rows = np.linspace(0, nrows, 20)
        # src_x, src_y = np.meshgrid(src_cols, src_rows)
        # src = np.dstack([src_y.flat, src_x.flat])[0]

        # dst_cols = np.linspace(0, ncols, 20)
        # dst_rows = np.linspace(0, nrows, 20)
        # dst_x, dst_y = np.meshgrid(dst_cols, dst_rows)
        # dst = np.dstack([dst_y.flat, dst_x.flat])[0]

        # tform = PiecewiseAffineTransform()
        # tform.estimate(src, dst)

        # return warp(buffer, tform, output_shape = (nrows, ncols))


        # distort: Callable[[Tuple[int,int]], Tuple[int,int]] = lambda coords : (int((math.tan((coords[0] - widthD2) / widthD2 * piD4) + 1) * widthD2), coords[1])
        
        # result = np.zeros_like(buffer)
        # for i in range(3):
        #     result[..., i] = scimg.geometric_transform(buffer[..., i], distort, order = 2)
            
        # return result
