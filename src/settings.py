import argparse

from enum import Enum

class Side(Enum):
    LEFT = 'left'
    RIGHT = 'right'
    WIDEVIEW = 'wideview'
    TOPVIEW = 'topview' 
    FULLSCREEN = 'fullscreen'

class Settings:
    def __init__(self) -> None:
        args = make_args()
        
        self.size = [int(x) for x in args.res.split('x')]
        self.fov: int = args.fov
        self.town: str = args.town
        self.host: str = args.host
        
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
        '--side',
        default=Side.LEFT.value,
        choices=[side.value for side in list(Side)],
        help='location of the mirror')
    argparser.add_argument(
        '--fov',
        default=65,
        type=int,
        help='FOV for camera')
    argparser.add_argument(
        '--res',
        metavar='WIDTHxHEIGHT',
        default='0x0',
        help='window resolution')
    argparser.add_argument(
        '--town',
        default=None,
        help='Carla map ID')
    argparser.add_argument(
        '--host',
        default='localhost',
        help='Carla IP, or localhost')
    argparser.add_argument(
        '--srvhost',
        default='localhost',
        help='IP of the PC running the LEFT mirror, or localhost')
    
    return argparser.parse_args()
