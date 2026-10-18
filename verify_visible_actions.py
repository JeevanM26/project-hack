import os, time, subprocess, win32gui, win32process, win32con, ctypes, psutil
import uiautomation as auto

user32 = ctypes.windll.user32
hdesk = user32.OpenDesktopW('default', 0, False, 0x1FF)
if hdesk:
    user32.SetThreadDesktop(hdesk)

def force_foreground_window(hwnd):
    if not hwnd or not win32gui.IsWindow(hwnd):
        return False
    try:
        # Check if minimized
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9) # SW_RESTORE
        else:
            user32.ShowWindow(hwnd, 5) # SW_SHOW
        
        # Win32 Alt-tab hack to bypass Windows SetForegroundWindow restriction
        user32.keybd_event(0x12, 0, 0, 0)
        user32.keybd_event(0x12, 0, 2, 0)
        user32.SetForegroundWindow(hwnd)
        user32.BringWindowToTop(hwnd)
        return True
    except Exception as e:
        print(f"force_foreground_window error on {hwnd}: {e}")
        return False

def get_visible_window_by_keywords(keywords):
    matches = []
    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            cls = win32gui.GetClassName(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            # Filter out 0-size or off-screen phantom windows
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            if width > 50 and height > 50:
                low_t = title.lower()
                low_c = cls.lower()
                for kw in keywords:
                    if kw.lower() in low_t or kw.lower() in low_c:
                        matches.append((hwnd, title, cls, rect))
                        break
    win32gui.EnumWindows(cb, None)
    return matches

print("=== VERIFYING VISIBLE PHYSICAL WINDOWS ===")

# 1. Bring Browser to Foreground
print("\n--- 1. BROWSER VISIBILITY ---")
browser_wins = get_visible_window_by_keywords(["edge", "chrome", "brave", "firefox"])
print(f"Found {len(browser_wins)} browser windows:", [(w[0], w[1], w[3]) for w in browser_wins])
if browser_wins:
    b_hwnd = browser_wins[0][0]
    ok = force_foreground_window(b_hwnd)
    rect = win32gui.GetWindowRect(b_hwnd)
    print(f"Brought browser hwnd {b_hwnd} to foreground! New Rect: {rect}")

# 2. Test Real Visible Notepad + Typing
print("\n--- 2. NOTEPAD VISIBILITY & TYPING ---")
notepad_wins = get_visible_window_by_keywords(["notepad"])
if not notepad_wins:
    subprocess.Popen(["explorer.exe", r"shell:AppsFolder\Microsoft.WindowsNotepad_8wekyb3d8bbwe!App"])
    time.sleep(1.8)
    notepad_wins = get_visible_window_by_keywords(["notepad"])

print(f"Found {len(notepad_wins)} Notepad windows:", [(w[0], w[1], w[3]) for w in notepad_wins])
if notepad_wins:
    np_hwnd = notepad_wins[0][0]
    force_foreground_window(np_hwnd)
    np_ctrl = auto.ControlFromHandle(np_hwnd)
    # Find Document or Edit control
    edit = np_ctrl.DocumentControl() or np_ctrl.EditControl()
    if edit.Exists(1, 0):
        print(f"Found Notepad Edit/Document control: {edit.Name}, Class: {edit.ClassName}")
        test_msg = "J.A.R.V.I.S. v11.0 GODMODE - VISIBLE USER DESKTOP CONFIRMED\n"
        try:
            vp = edit.GetValuePattern()
            curr = vp.Value or ""
            vp.SetValue(curr + test_msg)
            print("Successfully typed into Notepad via UIA ValuePattern!")
        except Exception:
            edit.SendKeys(test_msg)
            print("Typed into Notepad via SendKeys!")

# 3. Test Real Visible Calculator + UIA
print("\n--- 3. CALCULATOR VISIBILITY & AUTHENTIC UIA ---")
calc_ctrl = auto.WindowControl(searchDepth=3, RegexName=".*Calculator.*")
if not calc_ctrl.Exists(0, 0):
    subprocess.Popen(["calc.exe"])
    time.sleep(1.5)
    calc_ctrl = auto.WindowControl(searchDepth=3, RegexName=".*Calculator.*")

if calc_ctrl.Exists(1, 0):
    print(f"Calculator found! NativeHandle: {calc_ctrl.NativeWindowHandle}")
    force_foreground_window(calc_ctrl.NativeWindowHandle)
    rect = win32gui.GetWindowRect(calc_ctrl.NativeWindowHandle)
    print(f"Calculator visible rect: {rect}")
    
    # Click 125 * 8 =
    btn_map = {
        "1": "num1Button", "2": "num2Button", "5": "num5Button",
        "8": "num8Button", "*": "multiplyButton", "=": "equalButton", "C": "clearButton"
    }
    # Clear
    clr = calc_ctrl.ButtonControl(searchDepth=10, AutomationId="clearButton")
    if clr.Exists(0, 0):
        clr.Click()
        time.sleep(0.05)
    
    for ch in ["1", "2", "5", "*", "8", "="]:
        b = calc_ctrl.ButtonControl(searchDepth=10, AutomationId=btn_map[ch])
        if b.Exists(1, 0):
            b.Click()
            time.sleep(0.04)
    
    time.sleep(0.2)
    res = calc_ctrl.TextControl(searchDepth=10, AutomationId="CalculatorResults")
    if res.Exists(1, 0):
        print(f"Calculator authentic UIA result: {res.Name}")
    else:
        print("CalculatorResults element not found")
