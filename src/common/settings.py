import argparse

from typing import Optional
from enum import Enum

from src.common.user_action import UserAction

class MirrorType(Enum):
    LEFT = 'left'           # left with mirror frame
    RIGHT = 'right'         # right with mirror frame
    WIDEVIEW = 'wideview'   # central stack with mirror frame
    RLEFT = 'rleft'         # rectangular left
    RRIGHT = 'rright'       # rectangular right
    RREAR = 'rrear'         # rectangular rearview
    TOPVIEW = 'topview'     # view from the top (not a mirror)

class ScenarioType(Enum):
    APPROACH = 'approach'

class Settings:
    def __init__(self) -> None:
        args = make_args()
        
        self.size = [int(x) for x in args.res.split('x')]
        self.fov: int = args.fov
        self.pitch: Optional[float] = args.pitch
        self.yaw: Optional[float] = args.yaw
        self.is_fullscreen = args.fullscreen == True
        self.location = [int(x) for x in args.location.split(',')] if args.location else None
        self.offset = [int(x) for x in args.offset.split(',')] if args.offset else None

        self.screen: int = args.display
        self.use_smart_display: int = args.smart_display

        self.distortion: Optional[float] = args.distortion
        self.is_shader_control_by_mouse = args.mouse == True

        self.adopt_egocar = args.adopt_egocar == True
        self.is_manual_mode = args.manual == True

        self.town: Optional[str] = args.map
        self.host: str = args.host
        self.primary_mirror_host: str = args.pm_host
        self.scenario: Optional[str] = args.scenario

        if self.size[0] == 0 or self.size[1] == 0:
            self.size = None
            
        for type in list(MirrorType):
            if args.type == type.value:
                self.type = type
                break
        else:
            self.type = MirrorType.LEFT
        
def make_args():
    # _ w e _ _ y _ i _ _
    # _ s _ _ g _ j k _
    # z x c v b n _
    
    def to_key(code: int) -> str:
        if code == 27:
            return 'ESCAPE'
        elif code in range(32, 255):
            return chr(code)
        elif code in range(0x4000_003A, 0x4000_0049):
            return f'F_{code-0x4000_0039}'
        elif code == 0x4000_0050:
            return 'LEFT'
        elif code == 0x4000_004F:
            return 'RIGHT'
        elif code in range(0x4000_0058, 0x4000_0062):
            return f'KP_{code-0x4000_0058}'
        else:
            return '?' + str(code)
    
    shortcuts = [(to_key(key) + ' = ' + str(UserAction.SHORTCUTS[key].type).split('.')[1] + ' ' + (str(UserAction.SHORTCUTS[key].param or ' '))).ljust(78, chr(0xA0)) for key in UserAction.SHORTCUTS]
        
    argparser = argparse.ArgumentParser(
        description='CARLA mirror',
        epilog='Shortcuts:'.ljust(78, chr(0xA0)) + ' '.join(shortcuts),
    )
    
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
        help='Mirror camera resolution (default: defined for each mirror separately)')
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
        '-y',
        '--yaw',
        default=None,
        type=float,
        help='Camera yaw (default: dependant on the mirror)')
    argparser.add_argument(
        '-l',
        '--location',
        metavar='X,Y',
        default=None,
        help='Mirror X,Y location. If not specified, then either a default location is used, \
            or the location used previously')
    argparser.add_argument(
        '-o',
        '--offset',
        metavar='X,Y',
        default=None,
        help='Mirror X,Y offset for R-type mirrors. If not specified, then either a default \
            offset is used (0,0), or the offset used previously')
    argparser.add_argument(
        '-c',
        '--fullscreen',
        action='store_true',
        help='Enables full-screen view for R-type mirrors. Then size means the size of the camera image')

    argparser.add_argument(
        '-d',
        '--display',
        default=0,
        type=int,
        help='Screen to use (default: 0). Ignored if --smart-display is used')
    
    argparser.add_argument(
        '-sm',
        '--smart-display',
        action='store_true',
        help='Tries to reveal the display to use from the mirror type. So, left mirrors \
            will be shown on the left-bottom -most display, right mirror on the right-bottom -most \
            display, rear and wideview will be shown on the display below the main display, \
            other displays will be shown on the main display')
    
    # Mirror distortion features
    argparser.add_argument(
        '-q',
        '--distortion',
        default=None,
        const=0.0,
        nargs='?',
        type=float,
        help='Distort the mirror view. Default distortion of R-type mirrors is "linear + parabolic", \
            but if this parameter is provided with a value, then R-type mirrors use "circular" disrtortion \
            with the parameter value used as radius (default: no distortion)')
    argparser.add_argument(
        '-u',
        '--mouse',
        action='store_true',
        help='Enables shader control by mouse. Allows manipulating zoom rate with \
            mouse-scroll (all shaders) and distortion change point with mouse movements \
            (for "linear + parabolic" only)')
    
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
        help='A flag to indicate that this is the primary mirror, even though the driving car \
            exists already, which is usually the case when the manual driving mode is set')
    
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
        help='IP of the PC running the primary mirror (default: localhost). \
            Used when launching secondary mirrors only')
    argparser.add_argument(
        '-s',
        '--scenario',
        default=None,
        choices=[type.value for type in list(ScenarioType)],
        help='Scenarion to run. Empty argument means no scenario to execute')

    return argparser.parse_args()
