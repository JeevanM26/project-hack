import ctypes
import win32gui
import win32con
import psutil

hdesk = ctypes.windll.user32.OpenDesktopW('default', 0, False, 0x1FF)
if hdesk:
    ctypes.windll.user32.SetThreadDesktop(hdesk)

windows = []
def cb(h, _):
    if win32gui.IsWindowVisible(h):
        t = win32gui.GetWindowText(h)
        if t:
            windows.append((h, t))
win32gui.EnumWindows(cb, None)

for h, t in windows:
    clean_t = t.encode('ascii', 'ignore').decode()
    if clean_t.strip():
        print(f"HWND: {h} | Title: {clean_t}")
