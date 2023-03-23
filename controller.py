import pygame

from typing import List, Optional
from enum import IntEnum

class ActionType(IntEnum):
    NONE = 0
    QUIT = 1
    SPAWN_TARGET = 2
    SPAWN_CAR = 3
    PRINT_INFO = 4
    TOGGLE_NIGHT = 5
    SPAWN_TARGET_NEARBY = 6
    MOUSE = 16

class Action:
    def __init__(self, type: ActionType, param: Optional[str] = None):
        self.type = type
        self.param = param
        
class Controller:
    SPAWNABLES: List[str] = [
        'bin',
        'barrel',
        'clothcontainer',
        'trashcan01',
        'plastictable',
        'slide',
        'trampoline',
        'travelcase',
        'trafficcone01',
        'kiosk_01',
        'advertisement',
        'mailbox',
        'vendingmachine',
    ]
    
    @staticmethod
    def get_input() -> Optional[Action]:
        for event in pygame.event.get():
            if event.type == pygame.constants.QUIT:
                return Action(ActionType.QUIT)
            elif event.type == pygame.constants.MOUSEBUTTONDOWN:
                return Action(ActionType.MOUSE, 'down')
            elif event.type == pygame.constants.MOUSEMOTION:
                return Action(ActionType.MOUSE, 'move')
            elif event.type == pygame.constants.MOUSEBUTTONUP:
                return Action(ActionType.MOUSE, 'up')
            elif event.type == pygame.constants.KEYUP:
                if event.key == pygame.constants.K_ESCAPE:
                    return Action(ActionType.QUIT)
                elif event.key == pygame.constants.K_1:
                    return Action(ActionType.SPAWN_TARGET, Controller.SPAWNABLES[0])
                elif event.key == pygame.constants.K_2:
                    return Action(ActionType.SPAWN_TARGET, Controller.SPAWNABLES[1])
                elif event.key == pygame.constants.K_3:
                    return Action(ActionType.SPAWN_TARGET, Controller.SPAWNABLES[2])
                elif event.key == pygame.constants.K_4:
                    return Action(ActionType.SPAWN_TARGET, Controller.SPAWNABLES[3])
                elif event.key == pygame.constants.K_5:
                    return Action(ActionType.SPAWN_TARGET, Controller.SPAWNABLES[4])
                elif event.key == pygame.constants.K_6:
                    return Action(ActionType.SPAWN_TARGET, Controller.SPAWNABLES[5])
                elif event.key == pygame.constants.K_7:
                    return Action(ActionType.SPAWN_TARGET, Controller.SPAWNABLES[6])
                elif event.key == pygame.constants.K_8:
                    return Action(ActionType.SPAWN_TARGET, Controller.SPAWNABLES[7])
                elif event.key == pygame.constants.K_9:
                    return Action(ActionType.SPAWN_TARGET, Controller.SPAWNABLES[8])
                elif event.key == pygame.constants.K_0:
                    return Action(ActionType.SPAWN_TARGET, Controller.SPAWNABLES[9])
                elif event.key == pygame.constants.K_q:
                    return Action(ActionType.SPAWN_TARGET, Controller.SPAWNABLES[10])
                elif event.key == pygame.constants.K_w:
                    return Action(ActionType.SPAWN_TARGET, Controller.SPAWNABLES[11])
                elif event.key == pygame.constants.K_e:
                    return Action(ActionType.SPAWN_TARGET, Controller.SPAWNABLES[12])
                elif event.key == pygame.constants.K_p:
                    return Action(ActionType.SPAWN_TARGET_NEARBY, 'cottage')
                elif event.key == pygame.constants.K_x:
                    return Action(ActionType.PRINT_INFO)
                elif event.key == pygame.constants.K_c:
                    return Action(ActionType.TOGGLE_NIGHT)
                elif event.key == pygame.constants.K_n:
                    return Action(ActionType.SPAWN_CAR, 'behind')
                elif event.key == pygame.constants.K_m:
                    return Action(ActionType.SPAWN_CAR, 'random')
        return None
