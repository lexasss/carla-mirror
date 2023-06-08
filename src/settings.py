import argparse

from typing import Optional
from enum import Enum

class MirrorType(Enum):
    LEFT = 'left'           # left with mirror frame
    RIGHT = 'right'         # right with mirror frame
    WIDEVIEW = 'wideview'   # central stack with mirror frame
    RLEFT = 'rleft'         # rectangular left
    RRIGHT = 'rright'       # rectangular right
    RREAR = 'rrear'         # rectangular rearview
    TOPVIEW = 'topview'     # view from the top (not a mirror)

class Settings:
    def __init__(self) -> None:
        args = make_args()
        
        self.size = [int(x) for x in args.res.split('x')]
        self.fov: int = args.fov
        self.pitch: Optional[float] = args.pitch
        self.is_fullscreen = args.fullscreen == True

        self.screen: int = args.screen

        self.distort: bool = args.distort == True
        self.distortion_circle_radius: Optional[float] = args.circle_radius
        self.is_shader_control_by_mouse = args.mouse == True

        self.is_primary_mirror = args.adopt_egocar == True
        self.is_manual_mode = args.manual == True

        self.town: Optional[str] = args.map
        self.host: str = args.host
        self.primary_mirror_host: str = args.pm_host

        if self.size[0] == 0 or self.size[1] == 0:
            self.size = None
            
        for type in list(MirrorType):
            if args.type == type.value:
                self.type = type
                break
        else:
            self.type = MirrorType.LEFT
        
def make_args():
    #   w e     y   i o
    #         g   j k l
    # z x   v b
    argparser = argparse.ArgumentParser(
        description='CARLA mirror')
    
    # Mirror main features
    argparser.add_argument(
        '-t',
        '--type',
        default=MirrorType.LEFT.value,
        choices=[type.value for type in list(MirrorType)],
        help='Mirror type (default: left)')
    argparser.add_argument(
        '-r',
        '--res',
        metavar='WIDTHxHEIGHT',
        default='0x0',
        help='window resolution (default: defined for each mirror separately)')
    argparser.add_argument(
        '-f',
        '--fov',
        default=65,
        type=int,
        help='FOV for camera (default: 65)')
    argparser.add_argument(
        '-p',
        '--pitch',
        default=None,
        type=float,
        help='Camera pitch (default: dependant on FOV)')
    argparser.add_argument(
        '-n',
        '--fullscreen',
        action='store_true',
        help='Enables full-screen display for R-type mirrors. Then size means the size of the camera image')

    argparser.add_argument(
        '-c',
        '--screen',
        default=0,
        type=int,
        help='Screen to use (default: 0)')
    
    # Mirror distortion features
    argparser.add_argument(
        '-d',
        '--distort',
        action='store_true',
        help='Distort the mirror view. Default distortion is "linear + parabolic"')
    argparser.add_argument(
        '-q',
        '--circle-radius',
        default=None,
        type=float,
        help='Uses "circular" curvature instead of "linear + parabolic" with the radius specified here (default: None, i.e. non-circular curvature will be used)')
    argparser.add_argument(
        '-u',
        '--mouse',
        action='store_true',
        help='Enables shader control by mouse. Allows manipulating zoom rate (all shaders) and distortion change point (for "linear + parabolic" only)')
    
    # Driving features
    argparser.add_argument(
        '-m',
        '--manual',
        action='store_true',
        help='The flag to set the manual driving mode')
    argparser.add_argument(
        '-a',
        '--adopt-egocar',
        action='store_true',
        help='A flag to indicate that this is the primary mirror, even though the driving car exists already, which is usually the case when the manual driving mode is set')
    
    # Other options
    argparser.add_argument(
        '--map',
        default=None,
        help='CARLA`s map ID')
    argparser.add_argument(
        '--host',
        default='localhost',
        help='CARLA`s IP (default: localhost)')
    argparser.add_argument(
        '--pm-host',
        default='localhost',
        help='IP of the PC running the primary mirror (default: localhost). Used when launching secondary mirrors only')
    
    return argparser.parse_args()
