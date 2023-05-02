import pygame

from typing import Dict, Optional
from enum import IntEnum

class ActionType(IntEnum):
    NONE = 0
    QUIT = 1
    SPAWN_TARGET = 2
    SPAWN_CAR = 3
    PRINT_INFO = 4
    TOGGLE_NIGHT = 5
    SPAWN_TARGET_NEARBY = 6
    TOGGLE_MIRROR_DIMMING = 7
    MOUSE = 16
    MOUSEMOVE = 17

class Action:
    def __init__(self, type: ActionType, param: Optional[str] = None):
        self.type = type
        self.param = param

class Controller:
    SHORTCUTS: Dict[int, Action] = {
        pygame.constants.K_ESCAPE: Action(ActionType.QUIT),
        pygame.constants.K_1: Action(ActionType.SPAWN_TARGET, 'bin'),
        pygame.constants.K_2: Action(ActionType.SPAWN_TARGET, 'barrel'),
        pygame.constants.K_3: Action(ActionType.SPAWN_TARGET, 'clothcontainer'),
        pygame.constants.K_4: Action(ActionType.SPAWN_TARGET, 'trashcan01'),
        pygame.constants.K_5: Action(ActionType.SPAWN_TARGET, 'plastictable'),
        pygame.constants.K_6: Action(ActionType.SPAWN_TARGET, 'slide'),
        pygame.constants.K_7: Action(ActionType.SPAWN_TARGET, 'trampoline'),
        pygame.constants.K_8: Action(ActionType.SPAWN_TARGET, 'travelcase'),
        pygame.constants.K_9: Action(ActionType.SPAWN_TARGET, 'travelcase'),
        pygame.constants.K_0: Action(ActionType.SPAWN_TARGET, 'trafficcone01'),
        pygame.constants.K_q: Action(ActionType.SPAWN_TARGET, 'kiosk_01'),
        pygame.constants.K_w: Action(ActionType.SPAWN_TARGET, 'advertisement'),
        pygame.constants.K_e: Action(ActionType.SPAWN_TARGET, 'mailbox'),
        pygame.constants.K_p: Action(ActionType.SPAWN_TARGET_NEARBY, 'cottage'),
        pygame.constants.K_x: Action(ActionType.PRINT_INFO),
        pygame.constants.K_c: Action(ActionType.TOGGLE_NIGHT),
        pygame.constants.K_n: Action(ActionType.SPAWN_CAR, 'behind'),
        pygame.constants.K_m: Action(ActionType.SPAWN_CAR, 'random'),
        pygame.constants.K_BACKSLASH: Action(ActionType.TOGGLE_MIRROR_DIMMING)
    }
    
    @staticmethod
    def get_input() -> Optional[Action]:
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
               print(event)
            elif event.type == pygame.constants.KEYUP:
                if event.key in Controller.SHORTCUTS:
                    return Controller.SHORTCUTS[event.key]
        return None
