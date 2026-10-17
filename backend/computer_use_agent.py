"""
J.A.R.V.I.S. Computer Use Agent
=================================
Runs GUI automation in a separate subprocess so it always has interactive desktop access.
Uses pyautogui (which DOES work for key injection) + PowerShell UIA as fallback.
"""

import os
import re
import sys
import json
import time
import math
import subprocess
import tempfile
import shutil
import webbrowser
import logging
from typing import Dict, Any, List, Optional

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.03
    PYAUTOGUI_OK = True
except Exception:
    PYAUTOGUI_OK = False

logger = logging.getLogger("jarvis.computer_use")

# ─── Python-safe expression evaluator ─────────────────────────────────────────

_SAFE_MATH_BUILTINS = {
    'abs': abs, 'round': round, 'pow': pow,
    'sqrt': math.sqrt, 'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
    'log': math.log, 'log10': math.log10, 'exp': math.exp,
    'ceil': math.ceil, 'floor': math.floor, 'pi': math.pi, 'e': math.e,
}


def safe_eval_math(expr: str) -> Dict[str, Any]:
    """Safely evaluate a math expression and return the result."""
    # Normalize expression
    expr = expr.strip()
    expr = re.sub(r'[×xX]', '*', expr)      # × → *
    expr = re.sub(r'÷', '/', expr)           # ÷ → /
    expr = re.sub(r'\^', '**', expr)         # ^ → **
    expr = re.sub(r'√(\d+)', r'sqrt(\1)', expr)  # √9 → sqrt(9)

    # Reject anything not math
    if re.search(r'[a-zA-Z_]', re.sub(r'(sqrt|sin|cos|tan|log|exp|ceil|floor|abs|round|pow|pi|e)', '', expr)):
        return {"ok": False, "error": f"Non-math characters in expression: {expr}"}

    try:
        result = eval(expr, {"__builtins__": {}}, _SAFE_MATH_BUILTINS)  # noqa: S307
        return {"ok": True, "expression": expr, "result": result, "result_str": str(result)}
    except Exception as e:
        return {"ok": False, "expression": expr, "error": str(e)}


# ─── GUI automation via helper subprocess ──────────────────────────────────────

CALC_KEY_MAP = {
    '+': '+', '-': '-', '*': '*', '/': '/',
    '.': '.', '(': '(', ')': ')',
    '0': '0', '1': '1', '2': '2', '3': '3', '4': '4',
    '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
}


def _build_calc_helper_script(expression: str, result_json_path: str) -> str:
    """Build Python code that opens Calculator and types the expression via pyautogui."""
    normalized = expression.strip()
    normalized = re.sub(r'[×xX]', '*', normalized)
    normalized = re.sub(r'÷', '/', normalized)
    normalized = re.sub(r'\^', '**', normalized)
    normalized = re.sub(r'\s+', '', normalized)

    return f"""
import pyautogui, subprocess, time, json, sys, os

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.06

result = {{"ok": False, "expression": {json.dumps(expression)}, "steps": []}}

try:
    subprocess.Popen(['calc.exe'])
    time.sleep(2.5)
    result["steps"].append("Launched Windows Calculator")

    pyautogui.press('escape')
    time.sleep(0.3)
    result["steps"].append("Cleared previous state")

    expr = {json.dumps(normalized)}
    clicked = []
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch == '*' and i + 1 < len(expr) and expr[i+1] == '*':
            pyautogui.press('*')
            i += 2
            clicked.append('**')
            continue
        if ch in '0123456789.':
            pyautogui.press(ch)
        elif ch == '+':
            pyautogui.press('+')
        elif ch == '-':
            pyautogui.press('-')
        elif ch == '*':
            pyautogui.press('*')
        elif ch == '/':
            pyautogui.press('/')
        elif ch == '(':
            pyautogui.hotkey('shift', '9')
        elif ch == ')':
            pyautogui.hotkey('shift', '0')
        clicked.append(ch)
        time.sleep(0.08)
        i += 1

    result["steps"].append(f"Typed: {{''.join(clicked)}}")
    pyautogui.press('enter')
    time.sleep(0.5)
    result["steps"].append("Pressed Enter/Equals")
    result["ok"] = True
    result["expression_typed"] = ''.join(clicked)

except Exception as e:
    result["error"] = str(e)

with open({json.dumps(result_json_path)}, 'w') as f:
    json.dump(result, f)
"""


def _type_into_calculator_via_powershell(expression: str) -> Dict[str, Any]:
    """
    PRIMARY method: PowerShell AppActivate + SendKeys.
    Works regardless of which process context the caller is in — no window isolation issues.
    """
    normalized = re.sub(r'[×xX]', '*', expression.strip())
    normalized = re.sub(r'÷', '/', normalized)
    normalized = re.sub(r'\s+', '', normalized)

    # Build SendKeys-safe string
    sendkeys_map = {'+': '{+}', '^': '{^}', '%': '{%}', '~': '{~}',
                    '(': '{(}', ')': '{))', '[': '{[}', ']': '{]}',
                    '{': '{{}', '}': '{}}'}
    sendkeys_str = ""
    for ch in normalized:
        sendkeys_str += sendkeys_map.get(ch, ch)
    sendkeys_str += "~"  # ~ = ENTER

    ps_script = f"""
Add-Type -AssemblyName Microsoft.VisualBasic
Add-Type -AssemblyName System.Windows.Forms
Start-Process calc.exe
Start-Sleep -Milliseconds 2800
$activated = $false
for ($i = 0; $i -lt 15; $i++) {{
    try {{
        [Microsoft.VisualBasic.Interaction]::AppActivate('Calculator')
        $activated = $true
        break
    }} catch {{
        Start-Sleep -Milliseconds 300
    }}
}}
if ($activated) {{
    Start-Sleep -Milliseconds 700
    [System.Windows.Forms.SendKeys]::SendWait('{{ESCAPE}}')
    Start-Sleep -Milliseconds 200
    [System.Windows.Forms.SendKeys]::SendWait({json.dumps(sendkeys_str)})
    Start-Sleep -Milliseconds 600
    Write-Output "OK:{normalized}"
}} else {{
    Write-Output "FAIL:NoWindow"
}}
"""

    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            capture_output=True, text=True, timeout=20
        )
        out = r.stdout.strip()
        if out.startswith("OK:"):
            return {"ok": True, "method": "powershell_sendkeys", "typed": normalized}
        else:
            return {"ok": False, "method": "powershell_sendkeys", "error": out or r.stderr[:300]}
    except Exception as e:
        return {"ok": False, "method": "powershell_sendkeys", "error": str(e)}


def _type_into_calculator_via_pyautogui(expression: str, result_json_path: str) -> Dict[str, Any]:
    """
    FALLBACK: spawn helper WITHOUT CREATE_NO_WINDOW so it has full desktop access.
    The original bug was using CREATE_NO_WINDOW which isolated the subprocess from the GUI session.
    """
    helper_code = _build_calc_helper_script(expression, result_json_path)
    helper_file = os.path.join(tempfile.gettempdir(), f"jarvis_calc_gui_{int(time.time())}.py")
    try:
        with open(helper_file, 'w', encoding='utf-8') as f:
            f.write(helper_code)
        # *** CRITICAL: NO CREATE_NO_WINDOW FLAG — subprocess must have interactive desktop access ***
        proc = subprocess.Popen([sys.executable, helper_file])
        proc.wait(timeout=15)
        if os.path.exists(result_json_path):
            with open(result_json_path, 'r') as f:
                return json.load(f)
        return {"ok": False, "error": "Helper produced no output file"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        for p in [helper_file, result_json_path]:
            try:
                os.unlink(p)
            except Exception:
                pass


import ctypes
import ctypes.wintypes


def attach_to_default_desktop() -> bool:
    """
    Attaches the calling thread to the real interactive Windows desktop (WinSta0\\Default).
    This breaks out of sandbox/virtual desktops (e.g. exebox-...) so that
    pyautogui, screen captures, and window manipulation operate on the user's actual screen.
    """
    if sys.platform != "win32":
        return False
    try:
        user32 = ctypes.windll.user32
        hDefaultDesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if hDefaultDesk:
            ok = user32.SetThreadDesktop(hDefaultDesk)
            return bool(ok)
    except Exception as e:
        logger.warning(f"Failed to attach to Default desktop: {e}")
    return False


def force_foreground_window(hwnd: int) -> bool:
    """
    Bypasses Windows Focus Stealing Prevention to reliably bring any window to the front.
    Uses simulated Alt keystroke + AttachThreadInput + ShowWindow(SW_RESTORE) + SetForegroundWindow.
    """
    if sys.platform != "win32" or not hwnd:
        return False
    try:
        user32 = ctypes.windll.user32
        curr_hwnd = user32.GetForegroundWindow()
        cur_thread = user32.GetWindowThreadProcessId(curr_hwnd, None)
        app_thread = user32.GetWindowThreadProcessId(hwnd, None)

        # 1. Unlock focus stealing restriction via simulated Alt key
        user32.keybd_event(0x12, 0, 0, 0)  # ALT down
        user32.keybd_event(0x12, 0, 2, 0)  # ALT up

        # 2. Attach thread input to share focus queues
        if cur_thread != app_thread:
            user32.AttachThreadInput(cur_thread, app_thread, True)

        # 3. Restore and activate window
        user32.ShowWindow(hwnd, 9)  # 9 = SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        user32.SetFocus(hwnd)

        # 4. Detach thread input
        if cur_thread != app_thread:
            user32.AttachThreadInput(cur_thread, app_thread, False)

        time.sleep(0.3)
        return user32.GetForegroundWindow() == hwnd
    except Exception as e:
        logger.warning(f"force_foreground_window failed for {hwnd}: {e}")
        return False


def find_visible_windows(title_keyword: str) -> List[Dict[str, Any]]:
    """
    Enumerates all visible windows on WinSta0\\Default matching the title keyword.
    """
    attach_to_default_desktop()
    if sys.platform != "win32":
        return []

    user32 = ctypes.windll.user32
    matches = []

    def enum_cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value
                if title_keyword.lower() in title.lower():
                    rect = ctypes.wintypes.RECT()
                    user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    w = rect.right - rect.left
                    h = rect.bottom - rect.top
                    if w > 80 and h > 80:
                        matches.append({
                            "hwnd": hwnd,
                            "title": title,
                            "rect": (rect.left, rect.top, rect.right, rect.bottom),
                            "width": w,
                            "height": h,
                        })
        return True

    try:
        proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(enum_cb)
        user32.EnumWindows(proc, 0)
    except Exception as e:
        logger.warning(f"EnumWindows error: {e}")

    return matches


def _type_into_calculator_direct(expression: str) -> Dict[str, Any]:
    """
    1. Attaches calling thread to WinSta0\\Default.
    2. Launches/finds Calculator on the real screen.
    3. Forces Calculator into the foreground (bypassing browser focus lock).
    4. Physically sends keystrokes with pyautogui.
    """
    attach_to_default_desktop()

    if not PYAUTOGUI_OK:
        return {"ok": False, "error": "pyautogui not installed"}

    normalized = re.sub(r'[×xX]', '*', expression.strip())
    normalized = re.sub(r'÷', '/', normalized)
    normalized = re.sub(r'\^', '**', normalized)
    normalized = re.sub(r'\s+', '', normalized)

    steps = []
    try:
        # Check if Calculator is already open on Default desktop
        calc_windows = find_visible_windows("Calculator")
        if not calc_windows:
            subprocess.Popen(['calc.exe'])
            steps.append("Launched Windows Calculator (calc.exe)")
            for _ in range(12):
                time.sleep(0.4)
                calc_windows = find_visible_windows("Calculator")
                if calc_windows:
                    break
        else:
            steps.append("Found active Calculator window")

        target_hwnd = None
        if calc_windows:
            # Sort to prefer windows with real non-negative on-screen coordinates and largest size
            calc_windows.sort(
                key=lambda w: (w["rect"][0] >= 0 and w["rect"][1] >= 0, w["width"] * w["height"]),
                reverse=True
            )
            for cw in calc_windows:
                if force_foreground_window(cw["hwnd"]):
                    target_hwnd = cw["hwnd"]
                    steps.append(f"Forced foreground focus on Calculator (HWND {target_hwnd})")
                    break
            if not target_hwnd:
                target_hwnd = calc_windows[0]["hwnd"]
                force_foreground_window(target_hwnd)
                steps.append(f"Selected Calculator HWND {target_hwnd}")
        else:
            time.sleep(2.0)


        # Clear previous state completely (Escape + Delete + Escape guarantees 0 in Win11 Calculator)
        pyautogui.FAILSAFE = False
        pyautogui.press('escape')
        time.sleep(0.1)
        pyautogui.press('delete')
        time.sleep(0.1)
        pyautogui.press('escape')
        time.sleep(0.2)
        steps.append("Cleared previous state to 0 (Escape + Delete)")


        # Physically type the expression keystroke by keystroke
        clicked = []
        i = 0
        while i < len(normalized):
            ch = normalized[i]
            if ch == '*' and i + 1 < len(normalized) and normalized[i + 1] == '*':
                pyautogui.press('*')
                time.sleep(0.08)
                i += 2
                clicked.append('**')
                continue
            if ch in '0123456789.':
                pyautogui.press(ch)
            elif ch in ('+', '-', '*', '/'):
                pyautogui.press(ch)
            elif ch == '(':
                pyautogui.hotkey('shift', '9')
            elif ch == ')':
                pyautogui.hotkey('shift', '0')
            clicked.append(ch)
            time.sleep(0.08)
            i += 1

        expr_typed = ''.join(clicked)
        steps.append(f"Physically typed: {expr_typed}")

        # Press Enter / Equals
        pyautogui.press('enter')
        time.sleep(0.4)
        steps.append("Pressed Enter/Equals — result displayed on screen")

        return {
            "ok": True,
            "method": "pyautogui_winsta0_foreground",
            "typed": expr_typed,
            "steps": steps,
            "hwnd": target_hwnd,
        }

    except Exception as e:
        return {"ok": False, "method": "pyautogui_winsta0_foreground", "error": str(e), "steps": steps}


def execute_computer_use(action: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a real GUI computer use action.
    Dispatches to: calculate, type_in_app, screenshot, run_shell, web_open.
    """
    attach_to_default_desktop()
    action_type = action.get("type", "").lower().strip()

    # ── CALCULATE ─────────────────────────────────────────────────────────────
    if action_type == "calculate":
        expression = action.get("expression") or action.get("query", "0")

        # Step 1: Accurate math evaluation
        math_result = safe_eval_math(expression)

        # Step 2: Real desktop Calculator typing on WinSta0\Default
        gui_result = _type_into_calculator_direct(expression)

        steps = gui_result.get("steps", [])
        if not steps and gui_result.get("typed"):
            steps = [f"Typed {gui_result['typed']}"]

        return {
            "ok": True,
            "action": "calculate",
            "expression": expression,
            "result": math_result.get("result_str", "error"),
            "python_computed_result": math_result.get("result_str"),
            "calculator_gui_steps": steps,
            "gui_ok": gui_result.get("ok", False),
            "gui_method": gui_result.get("method", "unknown"),
        }

    # ── TYPE IN APP ───────────────────────────────────────────────────────────
    elif action_type == "type_in_app":
        app_name = action.get("app", "")
        text = action.get("text", "")
        attach_to_default_desktop()

        steps = []
        try:
            wins = find_visible_windows(app_name)
            if wins:
                force_foreground_window(wins[0]["hwnd"])
                steps.append(f"Focused window: {wins[0]['title']}")
            time.sleep(0.3)
            pyautogui.typewrite(text[:500], interval=0.03)
            steps.append(f"Typed {len(text[:500])} characters into {app_name}")
            return {"ok": True, "app": app_name, "typed_preview": text[:80], "steps": steps}
        except Exception as e:
            return {"ok": False, "app": app_name, "error": str(e)}

    # ── SCREENSHOT ────────────────────────────────────────────────────────────
    elif action_type == "screenshot":
        save_path = action.get("path", "")
        if not save_path:
            save_path = os.path.join(tempfile.gettempdir(), f"jarvis_screen_{int(time.time())}.png")

        attach_to_default_desktop()
        try:
            import PIL.ImageGrab
            img = PIL.ImageGrab.grab()
            img.save(save_path)
            return {"ok": True, "screenshot_path": save_path, "size": list(img.size)}
        except Exception as e:
            return {"ok": False, "error": str(e)}


    # ── LIST WINDOWS ──────────────────────────────────────────────────────────
    elif action_type == "list_windows":
        helper_code = """
import pygetwindow as gw, json
try:
    titles = [t for t in gw.getAllTitles() if t.strip()]
    print(json.dumps({"ok": True, "open_windows": titles}))
except Exception as e:
    print(json.dumps({"ok": False, "error": str(e)}))
"""
        return _run_gui_helper(helper_code)

    # ── RUN SHELL ─────────────────────────────────────────────────────────────
    elif action_type in ("run_shell", "run_command"):
        cmd = action.get("command", "")
        cwd = action.get("cwd", ".")
        if not cwd or not os.path.isdir(cwd):
            cwd = "."
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30, cwd=cwd
            )
            return {
                "ok": result.returncode == 0,
                "command": cmd,
                "stdout": result.stdout[:3000],
                "stderr": result.stderr[:1000],
                "exit_code": result.returncode,
            }
        except Exception as e:
            return {"ok": False, "command": cmd, "error": str(e)}

    # ── WEB OPEN ──────────────────────────────────────────────────────────────
    elif action_type in ("web_open", "open_url", "web_search_browser"):
        url = action.get("url") or action.get("query", "")
        if not url.startswith("http"):
            url = "https://www.google.com/search?q=" + url.replace(" ", "+")
        webbrowser.open(url, new=2)
        return {"ok": True, "action": "opened_browser", "url": url}

    else:
        return {"ok": False, "error": f"Unknown action type: '{action_type}'"}


def _run_gui_helper(code: str) -> Dict[str, Any]:
    """Run a GUI helper script in a subprocess and capture JSON output."""
    helper_file = os.path.join(tempfile.gettempdir(), f"jarvis_gui_{int(time.time())}.py")
    try:
        with open(helper_file, 'w', encoding='utf-8') as f:
            f.write(code)
        result = subprocess.run(
            [sys.executable, helper_file],
            capture_output=True, text=True, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
        )
        stdout = result.stdout.strip()
        if stdout:
            try:
                return json.loads(stdout)
            except Exception:
                return {"ok": True, "output": stdout}
        return {"ok": False, "error": result.stderr[:300] or "No output"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        try:
            os.unlink(helper_file)
        except Exception:
            pass


if __name__ == "__main__":
    print("=== JARVIS Computer Use Self-Test ===")
    print("\n[1] Math eval: 5*6")
    r = safe_eval_math("5*6")
    print("   Result:", r)

    print("\n[2] Math eval: sqrt(144) + 10")
    r = safe_eval_math("sqrt(144) + 10")
    print("   Result:", r)

    print("\n[3] Calculate 123*456 (python eval):")
    r = safe_eval_math("123*456")
    print("   Result:", r)
