import argparse

from enum import Enum

class Side(Enum):
    LEFT = 'left'
    RIGHT = 'right'
    WIDEVIEW = 'wideview'
    FULLSCREEN = 'fullscreen'

class Settings:
    def __init__(self) -> None:
        args = make_args()
        
        self.size = [int(x) for x in args.res.split('x')]
        if self.size[0] == 0 or self.size[1] == 0:
            self.size = None
        if args.side == Side.LEFT.value:
            self.side = Side.LEFT
        elif args.side == Side.LEFT.value:
            self.side = Side.RIGHT
        elif args.side == Side.WIDEVIEW.value:
            self.side = Side.WIDEVIEW
        elif args.side == Side.FULLSCREEN.value:
            self.side = Side.FULLSCREEN
        self.fov = args.fov
        self.town = args.town
        self.host = args.host


def make_args():
    argparser = argparse.ArgumentParser(
        description='CARLA mirror')
    argparser.add_argument(
        '--side',
        default=Side.LEFT.value,
        choices=[x.value for x in list(Side)],
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
    
    return argparser.parse_args()
