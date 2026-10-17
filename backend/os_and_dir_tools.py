import ast
import os
import platform
import re
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import pyautogui
    pyautogui.FAILSAFE = True
except Exception:
    pyautogui = None


COMMON_WINDOWS_APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calculator.exe": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "powershell": "powershell.exe",
    "terminal": "wt.exe",
    "windows terminal": "wt.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "brave": "brave",
    "firefox": "firefox",
    "spotify": "spotify:",
    "settings": "ms-settings:",
}


def open_system_app_or_url(target: str) -> Dict[str, Any]:
    """Physically opens any installed application, folder, or website URL on the user's laptop."""
    if sys.platform == "win32":
        try:
            from computer_use_agent import attach_to_default_desktop
            attach_to_default_desktop()
        except Exception:
            pass

    cleaned = target.strip().strip('"\'')
    cleaned = re.sub(r'[\.\?!,;]+$', '', cleaned).strip()
    lower = cleaned.lower()


    # 1. Check if it's a URL or website domain
    if lower.startswith(("http://", "https://")) or any(
        lower.endswith(ext) for ext in (".com", ".org", ".io", ".dev", ".ai", ".in", ".net")
    ):
        url = cleaned if lower.startswith(("http://", "https://")) else f"https://{cleaned}"
        webbrowser.open(url, new=2)
        return {"ok": True, "action": "opened_url", "target": url}

    # 2. Check if it's an existing file or directory path on disk
    if os.path.exists(cleaned):
        if sys.platform == "win32":
            os.startfile(os.path.abspath(cleaned))
        else:
            subprocess.Popen(["xdg-open", os.path.abspath(cleaned)])
        return {"ok": True, "action": "opened_path", "target": os.path.abspath(cleaned)}

    # 3. Robust conversational & platform normalization
    # Strip conversational prefixes: "open", "launch", "start", "run", "please"
    clean_app = re.sub(r'^(?:please\s+)?(?:open|launch|start|run)\s+', '', lower).strip()
    clean_app = re.sub(r'^(?:the|an|a)\s+', '', clean_app).strip()
    clean_app = re.sub(r'\s+(?:app|application|program|software)$', '', clean_app).strip()
    clean_app = re.sub(r'\bin\s+(?:the\s+|my\s+)?(?:system|laptop|pc|computer)\b', '', clean_app).strip()
    clean_app = re.sub(r'[\.\?!,;]+$', '', clean_app).strip()

    # Strip OS extensions (.app from macOS, .exe, .lnk, .bat, .cmd from Windows)
    clean_base = re.sub(r'\.(?:exe|app|lnk|bat|cmd)$', '', clean_app).strip()

    if not clean_base or clean_base in {'system', 'laptop', 'desktop', 'computer'}:
        clean_base = 'notepad'

    # Check mapped dictionary
    mapped = (
        COMMON_WINDOWS_APPS.get(lower)
        or COMMON_WINDOWS_APPS.get(clean_app)
        or COMMON_WINDOWS_APPS.get(clean_base)
        or COMMON_WINDOWS_APPS.get(clean_base.replace(" ", ""))
        or clean_base
    )

    if sys.platform == "win32":
        # Try direct os.startfile (works for registered apps, URI schemes like calc.exe, notepad.exe, spotify:, ms-settings:, chrome, etc.)
        try:
            os.startfile(mapped)
            return {"ok": True, "action": "os_startfile", "target": mapped}
        except Exception:
            pass

        # Try PATH executable lookup (e.g. code.cmd, wt.exe)
        which_bin = shutil.which(mapped) or shutil.which(f"{mapped}.exe") or shutil.which(clean_base) or shutil.which(cleaned)
        if which_bin:
            proc = subprocess.Popen([which_bin], shell=True)
            return {"ok": True, "action": "spawned_binary", "target": which_bin, "pid": proc.pid}

        # Dynamic PowerShell Get-StartApps lookup for any installed Windows Store / Desktop app
        search_term = clean_base or cleaned
        try:
            ps_cmd = (
                f"Get-StartApps | Where-Object {{$_.Name -match '{search_term}'}} "
                "| Select-Object -First 1 -ExpandProperty AppID"
            )
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=8)
            app_id = res.stdout.strip()
            if app_id:
                subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{app_id}"])
                return {"ok": True, "action": "launched_start_app", "target": search_term, "app_id": app_id}
        except Exception as e:
            return {"ok": False, "error": f"Failed to launch '{search_term}': {e}"}

    else:
        which_bin = shutil.which(mapped) or shutil.which(cleaned)
        if which_bin:
            proc = subprocess.Popen([which_bin])
            return {"ok": True, "action": "spawned_binary", "target": which_bin, "pid": proc.pid}

    return {"ok": False, "error": f"Application '{target}' was not found on this system."}


def inspect_directory_and_find_mistakes(directory_path: str) -> Dict[str, Any]:
    """Walks a real local directory, parses code files, and runs syntax/linter/pytest diagnostics to find real mistakes."""
    root = Path(directory_path).expanduser().resolve()
    if root.is_file():
        root = root.parent
    if not root.exists() or not root.is_dir():
        root = Path(".").resolve()

    skip_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "build"}
    code_extensions = {".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".json"}

    scanned_files: List[Dict[str, Any]] = []
    detected_mistakes: List[Dict[str, Any]] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fname in filenames:
            ext = Path(fname).suffix.lower()
            if ext not in code_extensions:
                continue
            fpath = Path(dirpath) / fname
            rel_path = str(fpath.relative_to(root))
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                detected_mistakes.append({"file": rel_path, "type": "ReadError", "detail": str(e)})
                continue

            lines = content.splitlines()
            file_info: Dict[str, Any] = {
                "path": rel_path,
                "lines": len(lines),
                "size_bytes": len(content),
                "preview": "\n".join(lines[:60]),
                "full_content": content[:12000],
            }

            if ext == ".py":
                try:
                    tree = ast.parse(content, filename=rel_path)
                    funcs = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                    file_info["functions"] = funcs
                    file_info["classes"] = classes
                except SyntaxError as se:
                    detected_mistakes.append({
                        "file": rel_path,
                        "line": se.lineno,
                        "type": "PythonSyntaxError",
                        "detail": f"{se.msg} at line {se.lineno}: {(se.text or '').strip()}",
                    })
            elif ext == ".json":
                import json
                try:
                    json.loads(content)
                except Exception as je:
                    detected_mistakes.append({
                        "file": rel_path,
                        "type": "JSONParseError",
                        "detail": str(je),
                    })

            scanned_files.append(file_info)
            if len(scanned_files) >= 50:
                break

    # Run pytest if test files exist in the directory
    pytest_output = ""
    has_py_tests = any("test" in f["path"].lower() and f["path"].endswith(".py") for f in scanned_files)
    if has_py_tests:
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "--tb=short"],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=30,
            )
            pytest_output = (proc.stdout + "\n" + proc.stderr).strip()
            if proc.returncode != 0:
                detected_mistakes.append({
                    "file": "pytest_suite",
                    "type": "FailingUnitTests",
                    "detail": pytest_output[-1500:],
                })
        except Exception as e:
            pytest_output = f"Pytest execution error: {e}"

    return {
        "ok": True,
        "directory": str(root),
        "file_count": len(scanned_files),
        "files": scanned_files,
        "detected_mistakes": detected_mistakes,
        "pytest_output": pytest_output,
    }


def write_file_to_disk(base_dir: str, relative_path: str, content: str) -> Dict[str, Any]:
    """Writes or updates a real file on disk and validates syntax if Python."""
    root = Path(base_dir).expanduser().resolve()
    target = (root / relative_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    ast_valid = True
    syntax_error = None
    if target.suffix.lower() == ".py":
        try:
            ast.parse(content, filename=str(target))
        except SyntaxError as e:
            ast_valid = False
            syntax_error = f"Line {e.lineno}: {e.msg}"

    return {
        "ok": ast_valid,
        "path": str(target),
        "relative_path": relative_path,
        "bytes_written": len(content),
        "syntax_error": syntax_error,
    }


def run_terminal_command(command: str, cwd: str = ".", timeout: int = 45) -> Dict[str, Any]:
    """Executes a real shell command inside the target directory and returns stdout, stderr, and exit_code."""
    # Normalize python3 → python on Windows (model hallucination prevention)
    if sys.platform == "win32":
        command = re.sub(r'^python3\b', 'python', command.strip())
    work_dir = str(Path(cwd).expanduser().resolve())

    try:
        proc = subprocess.run(
            command,
            cwd=work_dir,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "ok": proc.returncode == 0,
            "command": command,
            "cwd": work_dir,
            "exit_code": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
        }
    except Exception as e:
        return {"ok": False, "command": command, "cwd": work_dir, "exit_code": -1, "stdout": "", "stderr": str(e)}
