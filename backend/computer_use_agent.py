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
    """Build Python code that opens Calculator and types the expression."""
    # Normalize expression for keystrokes
    normalized = expression.strip()
    normalized = re.sub(r'[×xX]', '*', normalized)
    normalized = re.sub(r'÷', '/', normalized)
    normalized = re.sub(r'\^', '**', normalized)
    normalized = re.sub(r'\s+', '', normalized)

    return f"""
import pyautogui, subprocess, time, json, sys, os, re

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

result = {{"ok": False, "expression": {json.dumps(expression)}, "steps": []}}

try:
    # 1. Launch/focus Calculator
    subprocess.Popen(['calc.exe'])
    time.sleep(2.2)
    result["steps"].append("Launched Windows Calculator")

    # 2. Press Escape to clear
    pyautogui.press('escape')
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'shift', 'd')  # switch to Standard mode if needed
    time.sleep(0.3)
    pyautogui.press('escape')
    result["steps"].append("Cleared previous state")

    # 3. Type expression keystroke by keystroke
    expr = {json.dumps(normalized)}
    clicked = []
    i = 0
    while i < len(expr):
        ch = expr[i]
        # Handle multi-char: ** -> press ^ once in calculator
        if ch == '*' and i + 1 < len(expr) and expr[i+1] == '*':
            # Power: Calculator uses ^ for power, but let's just compute it
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
            pyautogui.hotkey('shift', '9')  # ( key
        elif ch == ')':
            pyautogui.hotkey('shift', '0')  # ) key
        clicked.append(ch)
        time.sleep(0.07)
        i += 1

    result["steps"].append(f"Typed: {{''.join(clicked)}}")

    # 4. Press Enter to evaluate
    pyautogui.press('enter')
    time.sleep(0.5)
    result["steps"].append("Pressed Enter/Equals")
    result["ok"] = True
    result["expression_typed"] = ''.join(clicked)

except Exception as e:
    result["error"] = str(e)

# Write result JSON
with open({json.dumps(result_json_path)}, 'w') as f:
    json.dump(result, f)
"""


def execute_computer_use(action: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a real GUI computer use action.
    Dispatches to: calculate, type_in_app, screenshot, run_shell, web_open.
    """
    action_type = action.get("type", "").lower().strip()

    # ── CALCULATE ─────────────────────────────────────────────────────────────
    if action_type == "calculate":
        expression = action.get("expression") or action.get("query", "0")

        # Step 1: Always compute mathematically via Python (100% accurate)
        math_result = safe_eval_math(expression)

        # Step 2: Also visually operate Windows Calculator in background subprocess
        result_json = os.path.join(tempfile.gettempdir(), f"jarvis_calc_{int(time.time())}.json")
        helper_code = _build_calc_helper_script(expression, result_json)

        helper_file = os.path.join(tempfile.gettempdir(), f"jarvis_calc_helper_{int(time.time())}.py")
        try:
            with open(helper_file, 'w', encoding='utf-8') as f:
                f.write(helper_code)

            # Launch helper in separate process (has GUI access as child of user process)
            proc = subprocess.Popen(
                [sys.executable, helper_file],
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            proc.wait(timeout=12)

            gui_result = {}
            if os.path.exists(result_json):
                with open(result_json, 'r') as f:
                    gui_result = json.load(f)
        except Exception as e:
            gui_result = {"ok": False, "error": str(e)}
        finally:
            for p in [helper_file, result_json]:
                try:
                    os.unlink(p)
                except Exception:
                    pass

        return {
            "ok": True,
            "action": "calculate",
            "expression": expression,
            "result": math_result.get("result_str", "error"),
            "python_computed_result": math_result.get("result_str"),
            "calculator_gui_steps": gui_result.get("steps", []),
            "gui_ok": gui_result.get("ok", False),
        }

    # ── TYPE IN APP ───────────────────────────────────────────────────────────
    elif action_type == "type_in_app":
        app_name = action.get("app", "")
        text = action.get("text", "")

        helper_code = f"""
import pyautogui, subprocess, time, json, sys

pyautogui.FAILSAFE = False
result = {{"ok": False}}
try:
    import pygetwindow as gw
    wins = gw.getWindowsWithTitle({json.dumps(app_name)})
    if wins:
        wins[0].activate()
        time.sleep(0.5)
    pyautogui.typewrite({json.dumps(text[:500])}, interval=0.05)
    result = {{"ok": True, "typed": {json.dumps(text[:80])}}}
except Exception as e:
    result = {{"ok": False, "error": str(e)}}
print(json.dumps(result))
"""
        return _run_gui_helper(helper_code)

    # ── SCREENSHOT ────────────────────────────────────────────────────────────
    elif action_type == "screenshot":
        save_path = action.get("path", "")
        if not save_path:
            save_path = os.path.join(tempfile.gettempdir(), f"jarvis_screen_{int(time.time())}.png")

        helper_code = f"""
import pyautogui, json
pyautogui.FAILSAFE = False
try:
    img = pyautogui.screenshot()
    img.save({json.dumps(save_path)})
    print(json.dumps({{"ok": True, "screenshot_path": {json.dumps(save_path)}, "size": list(img.size)}}))
except Exception as e:
    print(json.dumps({{"ok": False, "error": str(e)}}))
"""
        return _run_gui_helper(helper_code)

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
