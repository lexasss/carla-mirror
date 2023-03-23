import argparse

from enum import Enum

class Side(Enum):
    LEFT = 'left'
    RIGHT = 'right'

class Settings:
    def __init__(self) -> None:
        args = make_args()
        
        self.width, self.height = [int(x) for x in args.res.split('x')]
        self.side = Side.LEFT if args.side == Side.LEFT.value else Side.RIGHT
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
        default='640x480',
        help='window resolution (default: 640x480)')
    argparser.add_argument(
        '--town',
        default=None,
        help='Carla map ID')
    argparser.add_argument(
        '--host',
        default='localhost',
        help='Carla IP, or localhost')
    
    return argparser.parse_args()
