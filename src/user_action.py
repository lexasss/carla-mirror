import pygame

from typing import Optional, Union, Tuple, Dict
from enum import IntEnum

class ActionType(IntEnum):
    NONE = 0
    QUIT = 1

    MOUSE = 4
    MOUSEMOVE = 5
    MIRROR_VIEW_OFFSET = 6

    SPAWN_TARGET = 8
    SPAWN_TARGET_NEARBY = 9
    SPAWN_CAR = 10
    REMOVE_TARGETS = 11
    REMOVE_CARS = 12
    
    START_SCENARIO = 16
    STOP_SCENARIO = 17
    FREEZE = 18
    UNFREEZE = 19
    
    LANE_LEFT = 24
    LANE_RIGHT = 25
    
    PRINT_INFO = 32
    TOGGLE_NIGHT = 33
    TOGGLE_MIRROR_DIMMING = 34
    TOGGLE_SPECTATOR_AS_DRIVER = 35
    
    DEBUG_MIRROR = 64
    DEBUG_TASK_SCREEN = 65

class CarSpawningLocation:
    random = 'random'
    behind_next_lane = 'behind_next_lane'
    behind_same_lane = 'behind_same_lane'

class Action:
    def __init__(self, type: ActionType, param: Optional[Union[str, float, int, Tuple[Union[str, float, int, None], ...]]] = None):
        self.type = type
        self.param = param

class DriverTask:
    TARGETS: Dict[str, str] = {
        # 'bin': 'BIN',
        # 'barrel': 'BARREL',
        'clothcontainer': 'CLOTH CONTAINER',
        'glasscontainer': 'GLASS CONTAINER',
        # 'trashcan05': 'TRASH CAN',
        'plastictable': 'PLASTIC TABLE',
        'slide': 'SLIDE',
        'swingcouch': 'SWING COUCH',
        'trampoline': 'TRAMPOLINE',
        'travelcase': 'TRAVEL CASE',
        'trafficcone01': 'TRAFFIC CONE',
        # 'kiosk_01': 'KIOSK',
        'fountain': 'FOUNTAIN',
        # 'advertisement': 'ADVERTISEMENT',
        # 'mailbox': 'MAILBOX',
        'vendingmachine': 'VENDING MACHINE'
    }

class UserAction:
    SHORTCUTS: Dict[int, Action] = {
        pygame.constants.K_ESCAPE: Action(ActionType.QUIT),
        
        pygame.constants.K_F1: Action(ActionType.START_SCENARIO),
        pygame.constants.K_F2: Action(ActionType.STOP_SCENARIO),
        pygame.constants.K_F3: Action(ActionType.FREEZE),
        pygame.constants.K_F4: Action(ActionType.UNFREEZE),
        pygame.constants.K_F5: Action(ActionType.REMOVE_TARGETS),
        pygame.constants.K_F6: Action(ActionType.REMOVE_CARS),
        
        pygame.constants.K_1: Action(ActionType.SPAWN_TARGET, 'clothcontainer'),
        pygame.constants.K_2: Action(ActionType.SPAWN_TARGET, 'plastictable'),
        pygame.constants.K_3: Action(ActionType.SPAWN_TARGET, 'slide'),
        pygame.constants.K_4: Action(ActionType.SPAWN_TARGET, 'trampoline'),
        pygame.constants.K_5: Action(ActionType.SPAWN_TARGET, 'swingcouch'),
        pygame.constants.K_6: Action(ActionType.SPAWN_TARGET, 'travelcase'),
        pygame.constants.K_7: Action(ActionType.SPAWN_TARGET, 'glasscontainer'),
        pygame.constants.K_8: Action(ActionType.SPAWN_TARGET, 'trafficcone01'),
        pygame.constants.K_9: Action(ActionType.SPAWN_TARGET, 'fountain'),
        pygame.constants.K_0: Action(ActionType.SPAWN_TARGET, 'vendingmachine'),

        pygame.constants.K_q: Action(ActionType.PRINT_INFO, 'spawn'),
        pygame.constants.K_w: Action(ActionType.PRINT_INFO, 'landmarks'),
        pygame.constants.K_e: Action(ActionType.PRINT_INFO, 'lights'),
        pygame.constants.K_r: Action(ActionType.PRINT_INFO, 'topology'),
        pygame.constants.K_t: Action(ActionType.PRINT_INFO, 'waypoints'),
        pygame.constants.K_y: Action(ActionType.PRINT_INFO, 'egocar_waypoint'),
        pygame.constants.K_h: Action(ActionType.PRINT_INFO, 'target_waypoint'),
        
        pygame.constants.K_u: Action(ActionType.DEBUG_TASK_SCREEN, ('button', 'Done')),
        pygame.constants.K_i: Action(ActionType.DEBUG_TASK_SCREEN, ('quest', True)),
        pygame.constants.K_o: Action(ActionType.DEBUG_TASK_SCREEN, ('quest', False)),
        pygame.constants.K_p: Action(ActionType.DEBUG_TASK_SCREEN, ('message', 'Find something', DriverTask.TARGETS['clothcontainer'])),
        pygame.constants.K_j: Action(ActionType.DEBUG_MIRROR, 'snapshot'),
        
        pygame.constants.K_a: Action(ActionType.TOGGLE_NIGHT),
        pygame.constants.K_s: Action(ActionType.TOGGLE_SPECTATOR_AS_DRIVER),

        pygame.constants.K_n: Action(ActionType.SPAWN_CAR, (CarSpawningLocation.behind_next_lane, 35)),
        pygame.constants.K_m: Action(ActionType.SPAWN_CAR, (CarSpawningLocation.behind_same_lane, 35)),
        pygame.constants.K_COMMA: Action(ActionType.SPAWN_CAR, (CarSpawningLocation.random, 0)),
        pygame.constants.K_BACKSLASH: Action(ActionType.TOGGLE_MIRROR_DIMMING),
        pygame.constants.K_LEFT: Action(ActionType.LANE_LEFT),
        pygame.constants.K_RIGHT: Action(ActionType.LANE_RIGHT),

        pygame.constants.K_KP4: Action(ActionType.MIRROR_VIEW_OFFSET, 'l'),
        pygame.constants.K_KP6: Action(ActionType.MIRROR_VIEW_OFFSET, 'r'),
        pygame.constants.K_KP8: Action(ActionType.MIRROR_VIEW_OFFSET, 'u'),
        pygame.constants.K_KP2: Action(ActionType.MIRROR_VIEW_OFFSET, 'd'),
        pygame.constants.K_KP7: Action(ActionType.MIRROR_VIEW_OFFSET, 'lu'),
        pygame.constants.K_KP1: Action(ActionType.MIRROR_VIEW_OFFSET, 'ld'),
        pygame.constants.K_KP9: Action(ActionType.MIRROR_VIEW_OFFSET, 'ru'),
        pygame.constants.K_KP3: Action(ActionType.MIRROR_VIEW_OFFSET, 'rd'),
    }
    
    @staticmethod
    def get() -> Optional[Action]:
        for event in pygame.event.get():
            if event.type == pygame.constants.QUIT:
                return Action(ActionType.QUIT)
            elif event.type == pygame.constants.MOUSEBUTTONDOWN:
                if event.button == pygame.constants.BUTTON_LEFT:
                    return Action(ActionType.MOUSE, 'down')
                elif event.button == pygame.constants.BUTTON_WHEELDOWN:
                    return Action(ActionType.MOUSE, 'scroll_down')
            elif event.type == pygame.constants.MOUSEBUTTONUP:
                if event.button == pygame.constants.BUTTON_LEFT:
                    return Action(ActionType.MOUSE, 'up')
                elif event.button == pygame.constants.BUTTON_WHEELUP:
                    return Action(ActionType.MOUSE, 'scroll_up')
            elif event.type == pygame.constants.MOUSEMOTION:
                mouse = pygame.mouse.get_pos()
                return Action(ActionType.MOUSE, f'move{mouse[0]},{mouse[1]}')
            elif event.type == pygame.constants.MOUSEWHEEL:
               pass
            elif event.type == pygame.constants.KEYUP:
                if event.key in UserAction.SHORTCUTS:
                    return UserAction.SHORTCUTS[event.key]
        return None
