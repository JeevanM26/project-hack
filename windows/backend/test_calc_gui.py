"""
Standalone test: which approach can type into Calculator?
Run this DIRECTLY from a terminal: python test_calc_gui.py
"""
import subprocess, time, sys, json, os

EXPR = "5*3583"
print(f"Testing Calculator GUI automation for: {EXPR}")

# Method 1: pygetwindow + pyautogui
print("\n--- Method 1: pygetwindow + pyautogui ---")
try:
    import pygetwindow as gw
    import pyautogui
    pyautogui.FAILSAFE = False

    subprocess.Popen(['calc.exe'])
    time.sleep(2.5)

    # Find Calculator window by title
    wins = []
    for w in gw.getAllWindows():
        if w.title:
            print(f"  Found window: {repr(w.title)}")
        if 'calc' in w.title.lower() or 'calculator' in w.title.lower():
            wins.append(w)

    if wins:
        w = wins[0]
        print(f"  Activating: {w.title}")
        w.activate()
        time.sleep(0.8)
        pyautogui.press('escape')
        time.sleep(0.2)
        for ch in EXPR:
            if ch == '*':
                pyautogui.press('*')
            else:
                pyautogui.press(ch)
            time.sleep(0.1)
        pyautogui.press('enter')
        print("  Method 1: SUCCESS - typed expression")
    else:
        print("  Method 1: FAIL - no Calculator window found")
except Exception as e:
    print(f"  Method 1 EXCEPTION: {e}")
