from .logger import logger
from aqt.theme import theme_manager
from platform import system, version, release
from ctypes import *

dwmapi = None
## Darkmode windows titlebar thanks to @miere43
def set_dark_titlebar(window, dwmapi) -> None:
    if dwmapi:
        handler_window = c_void_p(int(window.winId()))
        DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = c_int(19)
        DWMWA_USE_IMMERSIVE_DARK_MODE = c_int(20)
        windows_version = int(version().split('.')[2])
        attribute = DWMWA_USE_IMMERSIVE_DARK_MODE if windows_version >= 18985 else DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1
        if windows_version >= 17763 and int(release()) >= 10:
            dwmapi.DwmSetWindowAttribute(handler_window, attribute, byref(c_int(1)), c_size_t(4))
def set_dark_titlebar_qt(obj, dwmapi, fix=True) -> None:
    if dwmapi and theme_manager.get_night_mode():
        set_dark_titlebar(obj, dwmapi)
        # Trick to refresh the titlebar after dark titlebar is set
        if fix:
            obj.showFullScreen()
            obj.showNormal()
if system() == "Windows" and theme_manager.get_night_mode():
    dwmapi = WinDLL("dwmapi")
    if dwmapi:
        dwmapi.DwmSetWindowAttribute.argtypes = [c_void_p, c_int, c_void_p, c_size_t]
        dwmapi.DwmSetWindowAttribute.restype = c_int
logger.debug(dwmapi)