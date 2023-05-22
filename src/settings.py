import argparse

from typing import Optional
from enum import Enum

class Side(Enum):
    LEFT = 'left'           # left with mirror frame
    RIGHT = 'right'         # right with mirror frame
    WIDEVIEW = 'wideview'   # central stack with mirror frame
    RLEFT = 'rleft'         # rectangular left
    RRIGHT = 'rright'       # rectangular right
    TOPVIEW = 'topview'     # view from the top (not a mirror)

class Settings:
    def __init__(self) -> None:
        args = make_args()
        
        self.size = [int(x) for x in args.res.split('x')]
        self.fov: int = args.fov
        self.map: Optional[str] = args.map
        self.host: str = args.host
        self.pitch = int(args.pitch) if args.pitch != '' else None
        self.distort: bool = args.distort == True
        self.is_primary_mirror = args.adopt_egocar == True
        
        self.server_host: str = args.srvhost

        if self.size[0] == 0 or self.size[1] == 0:
            self.size = None
        for side in list(Side):
            if args.side == side.value:
                self.side = side
                break
        else:
            self.side = Side.LEFT
        
def make_args():
    argparser = argparse.ArgumentParser(
        description='CARLA mirror')
    argparser.add_argument(
        '-s',
        '--side',
        default=Side.LEFT.value,
        choices=[side.value for side in list(Side)],
        help='location of the mirror (default: left)')
    argparser.add_argument(
        '-f',
        '--fov',
        default=65,
        type=int,
        help='FOV for camera (default: 65)')
    argparser.add_argument(
        '-p',
        '--pitch',
        default='',
        type=str,
        help='Camera pitch')
    argparser.add_argument(
        '-d',
        '--distort',
        action='store_true',
        help='Distort the mirror view')
    argparser.add_argument(
        '-r',
        '--res',
        metavar='WIDTHxHEIGHT',
        default='0x0',
        help='window resolution')
    argparser.add_argument(
        '-m',
        '--map',
        default=None,
        help='Carla map ID')
    argparser.add_argument(
        '--host',
        default='localhost',
        help='Carla IP, or "localhost"')
    argparser.add_argument(
        '--srvhost',
        default='localhost',
        help='IP of the PC running the primary mirror, or localhost')
    argparser.add_argument(
        '-a',
        '--adopt-egocar',
        action='store_true',
        help='A flag to indicate that this is the primary mirror, even though the driving car exists already')
    
    return argparser.parse_args()
