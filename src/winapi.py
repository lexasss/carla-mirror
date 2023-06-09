from typing import Optional, Tuple

try:
    import win32api
    import win32con
    import win32gui
except ImportError:
    raise RuntimeError('pywin32 is not installed')

class Window:
    def __init__(self, size: Tuple[int, int], hwnd: Optional[int] = None):
        self.hwnd: int = win32gui.CreateWindowEx(0, '#32769', '', win32con.WS_MAXIMIZE | win32con.WS_VISIBLE, 0, 0, size[0], size[1], 0, 0, 0, None) if hwnd is None else hwnd
    
    def close(self):
        win32gui.DestroyWindow(self.hwnd)

    def set_location(self, x: int, y: int, is_topmost: bool):
        zorder = win32con.HWND_TOPMOST if is_topmost else win32con.HWND_TOP
        win32gui.SetWindowPos(self.hwnd, zorder, x, y, 0, 0, win32con.SWP_NOSIZE)

    def set_transparent_color(self, color: Tuple[int, int, int]) -> None:
        exstyle: int = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, exstyle | win32con.WS_EX_LAYERED)
        win32gui.SetLayeredWindowAttributes(self.hwnd, win32api.RGB(*color), 0, win32con.LWA_COLORKEY)

    def get_location(self) -> Tuple[int, int]:
        rect = win32gui.GetWindowRect(self.hwnd)
        return rect[0], rect[1]
