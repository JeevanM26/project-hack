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


def _type_into_calculator_direct(expression: str) -> Dict[str, Any]:
    """
    Open Calculator and type expression DIRECTLY using pyautogui in-process.
    pyautogui.press() uses Win32 SendInput which sends to the current foreground window
    on the real desktop — no window enumeration needed, works from any process context.
    """
    if not PYAUTOGUI_OK:
        return {"ok": False, "error": "pyautogui not installed"}

    normalized = re.sub(r'[×xX]', '*', expression.strip())
    normalized = re.sub(r'÷', '/', normalized)
    normalized = re.sub(r'\^', '**', normalized)
    normalized = re.sub(r'\s+', '', normalized)

    steps = []
    try:
        # Launch Calculator — it will come to the foreground automatically
        subprocess.Popen(['calc.exe'])
        steps.append("Launched Windows Calculator")
        # Wait long enough for Calculator to fully render and be in foreground
        time.sleep(3.0)

        # Clear any previous calculation
        pyautogui.press('escape')
        time.sleep(0.3)
        steps.append("Cleared previous state")

        # Type the expression character by character into the foreground window
        clicked = []
        i = 0
        while i < len(normalized):
            ch = normalized[i]
            if ch == '*' and i + 1 < len(normalized) and normalized[i+1] == '*':
                # ** (power) — just use * twice since calc doesn't have ^
                pyautogui.press('*')
                time.sleep(0.08)
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
            time.sleep(0.09)
            i += 1

        expr_typed = ''.join(clicked)
        steps.append(f"Typed: {expr_typed}")

        # Press Enter to evaluate
        pyautogui.press('enter')
        time.sleep(0.5)
        steps.append("Pressed Enter — result shown in Calculator display")

        return {"ok": True, "method": "pyautogui_direct", "typed": expr_typed, "steps": steps}

    except Exception as e:
        return {"ok": False, "method": "pyautogui_direct", "error": str(e), "steps": steps}


def execute_computer_use(action: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a real GUI computer use action.
    Dispatches to: calculate, type_in_app, screenshot, run_shell, web_open.
    """
    action_type = action.get("type", "").lower().strip()

    # ── CALCULATE ─────────────────────────────────────────────────────────────
    if action_type == "calculate":
        expression = action.get("expression") or action.get("query", "0")

        # Step 1: Python math — always 100% correct (instant)
        math_result = safe_eval_math(expression)

        # Step 2: Type into Calculator DIRECTLY via pyautogui in-process
        # pyautogui.SendInput goes to the foreground window — no subprocess, no isolation issues
        gui_result = _type_into_calculator_direct(expression)

        # Step 3: PowerShell AppActivate fallback if pyautogui failed for some reason
        if not gui_result.get("ok"):
            logger.warning(f"Direct pyautogui failed ({gui_result.get('error')}) — trying PowerShell fallback")
            gui_result = _type_into_calculator_via_powershell(expression)

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
