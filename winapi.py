import os

from typing import Optional, Tuple

if os.name == 'nt':
    import win32api
    import win32con
    import win32gui
else:
    raise Exception('This app should run on a Windows machine')

class Window:
    def __init__(self, hwnd: Optional[int] = None):
        self.hwnd: int = win32gui.CreateWindowEx(0, '#32769', '', win32con.WS_MAXIMIZE | win32con.WS_VISIBLE, 0, 0, 1920, 1024, 0, 0, 0, None) if hwnd is None else hwnd
    
    def close(self):
        win32gui.DestroyWindow(self.hwnd)

    def set_location(self, x: int, y: int):
        win32gui.SetWindowPos(self.hwnd, -1, x, y, 0, 0, 0x0001)

    def set_transparent_color(self, color: Tuple[int, int, int]) -> None:
        exstyle: int = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, exstyle | win32con.WS_EX_LAYERED)
        win32gui.SetLayeredWindowAttributes(self.hwnd, win32api.RGB(*color), 0, win32con.LWA_COLORKEY)

    def get_location(self) -> Tuple[int, int]:
        rect = win32gui.GetWindowRect(self.hwnd)
        return rect[0], rect[1]