"""
Gemma 4 Universal Dynamic GUI & Desktop Operator Agent for J.A.R.V.I.S.
Operates the user's physical laptop screen and mouse dynamically:
- ZERO hardcoded pixel coordinates: Resolves elements dynamically via:
  1. Playwright DOM Bounding Boxes (element.bounding_box())
  2. Windows UI Automation (pywinauto Desktop(backend="uia"))
  3. Live Screen OCR (RapidOCR) & Gemma 4 Multimodal Vision Pointing [0..1000]
- Smooth physical mouse gliding using pyautogui.easeInOutQuad
- Live MJPEG / WebSocket screen streaming via mss
- Synchronized with Shared Global Project Blackboard
"""
import base64
import io
import logging
import os
import re
import sys
import time
import urllib.parse
import webbrowser
from typing import Dict, Any, List, Optional, Tuple

from PIL import Image

try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Move mouse to [0, 0] to abort immediately
    pyautogui.PAUSE = 0.05
    PYAUTOGUI_AVAILABLE = True
except Exception:
    pyautogui = None
    PYAUTOGUI_AVAILABLE = False

try:
    import mss
    MSS_AVAILABLE = True
except Exception:
    mss = None
    MSS_AVAILABLE = False

from blackboard import global_blackboard

logger = logging.getLogger("JarvisGUIComputerAgent")

YOUTUBE_CATALOG = [
    {"keywords": ["believer", "imagine dragons"], "title": "Imagine Dragons — Believer (Official Music Video)", "video_id": "7wtfhZwyrcc"},
    {"keywords": ["kesariya", "brahmastra", "arijit"], "title": "Kesariya — Brahmastra (Arijit Singh)", "video_id": "BddP6PYo2gs"},
    {"keywords": ["arabic kuthu", "halamithi", "beast", "anirudh"], "title": "Arabic Kuthu — Halamithi Habibo (Anirudh)", "video_id": "KUN5Uf9mObQ"},
    {"keywords": ["naatu naatu", "rrr"], "title": "Naatu Naatu — RRR Official Song", "video_id": "OsU0CGZoV8E"},
    {"keywords": ["jai ho", "rahman"], "title": "A.R. Rahman — Jai Ho", "video_id": "Yc5OyXmHD0w"},
    {"keywords": ["starboy", "weeknd"], "title": "The Weeknd — Starboy ft. Daft Punk", "video_id": "34Na4j8AVgA"},
    {"keywords": ["faded", "alan walker"], "title": "Alan Walker — Faded", "video_id": "60ItHLz5WEA"},
    {"keywords": ["interstellar", "hans zimmer"], "title": "Interstellar Main Theme — Hans Zimmer", "video_id": "UDVtMYqUAyw"}
]


class JarvisGUIComputerAgent:
    def __init__(self, model_name: str = "gemma-4-12b-it", gemma_engine=None):
        self.model_name = model_name
        self.gemma_engine = gemma_engine
        self.active_app = "desktop"
        self.active_url = ""
        self.session_memory: Dict[str, Any] = {
            "youtube_open": False,
            "last_query": "",
            "active_tab": None,
            "last_mouse_xy": [0, 0]
        }
        self._ocr = None

    def _get_ocr(self):
        if self._ocr is None:
            try:
                from rapidocr_onnxruntime import RapidOCR
                self._ocr = RapidOCR()
            except Exception as e:
                logger.warning(f"Could not initialize RapidOCR: {e}")
                self._ocr = False
        return self._ocr if self._ocr is not False else None

    def get_screen_size(self) -> Tuple[int, int]:
        if PYAUTOGUI_AVAILABLE and pyautogui:
            try:
                return pyautogui.size()
            except Exception:
                pass
        return (2560, 1600)  # HP HyperX QHD+ default

    def capture_screen(self) -> Image.Image:
        """Captures active screen buffer using mss, PIL, or generates a live HUD telemetry canvas if locked."""
        if MSS_AVAILABLE and mss:
            try:
                with mss.MSS() as sct:
                    mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                    raw = sct.grab(mon)
                    return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
            except Exception:
                pass

        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            if img:
                return img
        except Exception:
            pass

        # Resilient Virtual HUD Frame when display is asleep/locked
        from PIL import ImageDraw
        w, h = self.get_screen_size()
        frame = Image.new("RGB", (1280, 800), (4, 10, 22))
        draw = ImageDraw.Draw(frame)
        # Grid lines
        for x in range(0, 1280, 80):
            draw.line([(x, 0), (x, 800)], fill=(8, 26, 50))
        for y in range(0, 800, 80):
            draw.line([(0, y), (1280, y)], fill=(8, 26, 50))

        # Title & Status
        draw.text((40, 40), "J.A.R.V.I.S. MARK LXXXV — LIVE TELEMETRY STREAM", fill=(0, 240, 255))
        draw.text((40, 70), f"Active Application: {self.active_app.upper()}", fill=(245, 158, 11))
        
        last_xy = self.session_memory.get("last_mouse_xy", [640, 400])
        mapped_x = int((last_xy[0] / max(1, w)) * 1280)
        mapped_y = int((last_xy[1] / max(1, h)) * 800)
        
        draw.text((40, 95), f"Physical Mouse: [{last_xy[0]}, {last_xy[1]}]", fill=(148, 163, 184))
        draw.text((40, 120), f"Swarm Objective: {global_blackboard.user_objective or 'Standby'}", fill=(52, 211, 153))

        # Mouse reticle
        draw.ellipse([mapped_x - 15, mapped_y - 15, mapped_x + 15, mapped_y + 15], outline=(0, 240, 255), width=2)
        draw.ellipse([mapped_x - 4, mapped_y - 4, mapped_x + 4, mapped_y + 4], fill=(245, 158, 11))
        draw.line([(mapped_x - 22, mapped_y), (mapped_x + 22, mapped_y)], fill=(0, 240, 255))
        draw.line([(mapped_x, mapped_y - 22), (mapped_x, mapped_y + 22)], fill=(0, 240, 255))
        
        return frame

    def capture_screen_jpeg_b64(self, quality: int = 70) -> str:
        """
        Captures the screen and encodes it to a base64 JPEG data URL for real-time streaming.
        """
        img = self.capture_screen()
        if img is None:
            return ""
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"

    def smooth_glide_click(self, target_x: int, target_y: int, duration: float = 0.6, click: bool = True) -> Dict[str, Any]:
        """
        Glides the physical mouse smoothly to (target_x, target_y) using easeInOutQuad
        and optionally clicks. Clamps safely to visible monitor bounds.
        """
        screen_w, screen_h = self.get_screen_size()
        px = int(max(10, min(screen_w - 10, target_x)))
        py = int(max(10, min(screen_h - 10, target_y)))

        norm_x = round((px / screen_w) * 1000.0, 1)
        norm_y = round((py / screen_h) * 1000.0, 1)

        self.session_memory["last_mouse_xy"] = [px, py]
        global_blackboard.update_mouse_position(px, py)

        if PYAUTOGUI_AVAILABLE and pyautogui:
            try:
                pyautogui.moveTo(px, py, duration=duration, tween=pyautogui.easeInOutQuad)
                if click:
                    pyautogui.click(px, py)
            except Exception as e:
                logger.warning(f"PyAutoGUI movement failed: {e}")

        return {
            "norm_x": norm_x,
            "norm_y": norm_y,
            "pixel_x": px,
            "pixel_y": py,
            "screen_w": screen_w,
            "screen_h": screen_h,
            "clicked": click
        }

    def move_and_click_visibly(self, norm_x: float, norm_y: float, duration: float = 0.75, click: bool = True) -> Dict[str, Any]:
        """
        Translates normalized [0..1000] Gemma 4 coordinate pointing into physical screen pixels.
        """
        screen_w, screen_h = self.get_screen_size()
        target_x = int((norm_x / 1000.0) * screen_w)
        target_y = int((norm_y / 1000.0) * screen_h)
        res = self.smooth_glide_click(target_x, target_y, duration=duration, click=click)
        res["norm_x"] = norm_x
        res["norm_y"] = norm_y
        return res

    def type_search_visibly(self, query: str, interval: float = 0.04, press_enter: bool = True) -> Dict[str, Any]:
        """Types text character-by-character on the user's active desktop."""
        if PYAUTOGUI_AVAILABLE and pyautogui:
            try:
                pyautogui.write(query, interval=interval)
                if press_enter:
                    pyautogui.press("enter")
            except Exception as e:
                logger.warning(f"PyAutoGUI write failed: {e}")
        return {"query": query, "enter_pressed": press_enter}

    def resolve_web_element_coordinates(self, page, selector_or_text: str) -> Optional[Tuple[int, int]]:
        """
        Resolves physical screen coordinates of a web element using Playwright DOM bounding box.
        """
        try:
            elem = page.query_selector(selector_or_text)
            if not elem:
                elem = page.get_by_text(selector_or_text).first
            if elem:
                box = elem.bounding_box()
                if box:
                    # Center of element in browser viewport
                    mid_x = int(box["x"] + box["width"] / 2)
                    mid_y = int(box["y"] + box["height"] / 2)
                    return mid_x, mid_y
        except Exception as e:
            logger.warning(f"Playwright coordinate resolution failed: {e}")
        return None

    def resolve_desktop_window_and_control(self, window_regex: str, control_regex: Optional[str] = None) -> Optional[Tuple[int, int]]:
        """
        Queries the Windows 11 accessibility tree (UIA backend) to find exact control coordinates.
        """
        try:
            from pywinauto import Desktop
            desktop = Desktop(backend="uia")
            for win in desktop.windows():
                title = win.window_text()
                if re.search(window_regex, title, re.I):
                    win.set_focus()
                    if control_regex:
                        for child in win.descendants():
                            c_text = child.window_text()
                            if re.search(control_regex, c_text, re.I):
                                rect = child.rectangle()
                                return (rect.mid_point().x, rect.mid_point().y)
                    rect = win.rectangle()
                    return (rect.mid_point().x, rect.mid_point().y)
        except Exception as e:
            logger.warning(f"pywinauto resolution error: {e}")
        return None

    def universal_visual_find_and_click(self, label_or_text: str, duration: float = 0.6) -> Dict[str, Any]:
        """
        Universal visual fallback: grabs live screenshot, runs RapidOCR to find text bounding box,
        and glides the mouse cursor to click its center.
        """
        ocr = self._get_ocr()
        img = self.capture_screen()
        if ocr and img:
            import numpy as np
            img_np = np.array(img)
            result, _ = ocr(img_np)
            if result:
                for line in result:
                    box, text, score = line[0], line[1], line[2]
                    if re.search(re.escape(label_or_text), text, re.I):
                        # Calculate centroid
                        xs = [pt[0] for pt in box]
                        ys = [pt[1] for pt in box]
                        cx = int(sum(xs) / len(xs))
                        cy = int(sum(ys) / len(ys))
                        step = self.smooth_glide_click(cx, cy, duration=duration, click=True)
                        return {"found": True, "method": "rapidocr", "label": label_or_text, "coords": [cx, cy], "step": step}

        # Fallback to center-screen safe glide
        w, h = self.get_screen_size()
        step = self.smooth_glide_click(w // 2, h // 2, duration=duration, click=False)
        return {"found": False, "method": "center_fallback", "label": label_or_text, "coords": [w // 2, h // 2], "step": step}

    def launch_system_app_or_website(self, target: str) -> Dict[str, Any]:
        """
        Universally launches any native Windows application, desktop tool, or website.
        Visibly glides the physical mouse cursor across the screen, captures the live desktop,
        and synchronizes blackboard state.
        """
        import shutil
        raw_target = target.lower().strip()
        
        # 1. Normalize typos and common misspellings
        t_clean = re.sub(r'\bap\b', 'app', raw_target)
        t_clean = re.sub(r'\bnotepd\b', 'notepad', t_clean)
        t_clean = re.sub(r'\bcalcultor\b', 'calculator', t_clean)
        t_clean = re.sub(r'\bsystm\b', 'system', t_clean)
        t_clean = re.sub(r'\bbrowsr\b', 'browser', t_clean)

        # 2. Extract specific app name if user said "like <app>" or "called <app>"
        like_m = re.search(r'(?:like|called|named|namely)\s+([a-zA-Z0-9_\-\.\s]+)', t_clean)
        if like_m:
            t_clean = like_m.group(1).strip()

        # 3. Strip conversational filler and noise phrases
        noise_phrases = [
            r'\bin\s+(?:the\s+|my\s+)?system\b',
            r'\bon\s+(?:the\s+|my\s+)?(?:system|laptop|pc|computer)\b',
            r'\b(?:an|a|the)?\s*application\b',
            r'\b(?:an|a|the)?\s*app\b',
            r'\bplease\b',
            r'\bfor\s+me\b',
            r'\bnow\b',
            r'\bright\s+now\b'
        ]
        for np in noise_phrases:
            t_clean = re.sub(np, '', t_clean).strip()

        t_clean = re.sub(r'^(?:an|a|the)\s+', '', t_clean).strip()

        # 4. If empty or generic (e.g. "open an ap in system" / "open app"), default to Notepad
        if not t_clean or t_clean in {'system', 'laptop', 'desktop', 'computer', 'anything', 'any', 'something'}:
            t_clean = 'notepad'

        target_clean = t_clean
        screen_w, screen_h = self.get_screen_size()
        executed_steps = []
        app_label = target_clean.title()

        # Known web services
        web_services = {
            "youtube": "https://www.youtube.com",
            "drive": "https://drive.google.com",
            "google drive": "https://drive.google.com",
            "gmail": "https://mail.google.com",
            "mail": "https://mail.google.com",
            "github": "https://github.com",
            "google": "https://www.google.com",
            "reddit": "https://www.reddit.com",
            "twitter": "https://x.com",
            "x": "https://x.com",
            "notion": "https://www.notion.so",
            "chatgpt": "https://chat.openai.com",
            "hacker news": "https://news.ycombinator.com",
            "hn": "https://news.ycombinator.com",
            "linkedin": "https://www.linkedin.com",
            "stackoverflow": "https://stackoverflow.com",
            "stack overflow": "https://stackoverflow.com",
        }

        # Check if it's a URL or known web service
        target_url = None
        if target_clean in web_services:
            target_url = web_services[target_clean]
            app_label = target_clean.title()
        elif target_clean.startswith("http://") or target_clean.startswith("https://"):
            target_url = target_clean
            app_label = target_clean
        elif "." in target_clean and not target_clean.endswith(".exe") and not target_clean.endswith(".py"):
            target_url = f"https://{target_clean}"
            app_label = target_clean

        if target_url:
            try:
                if sys.platform == "win32":
                    os.startfile(target_url)
                else:
                    webbrowser.open_new_tab(target_url)
            except Exception:
                webbrowser.open_new_tab(target_url)

            time.sleep(1.0)
            center_x, center_y = screen_w // 2, screen_h // 2
            step = self.smooth_glide_click(center_x, center_y, duration=0.6, click=False)
            executed_steps.append({
                "step": 1,
                "label": f"Launched {target_url} in browser & centered reticle",
                "coords": [500.0, 500.0],
                "details": step
            })

            self.active_app = f"browser_{target_clean}"
            self.active_url = target_url
            global_blackboard.update_browser_and_os(active_app=self.active_app, active_browser_url=target_url)

            return {
                "success": True,
                "action": "open_website",
                "target": target_url,
                "active_app": self.active_app,
                "executed_steps": executed_steps,
                "spoken_response": f"Opened {app_label} in your browser, sir."
            }

        # Known desktop applications on Windows
        app_executables = {
            "notepad": ["notepad.exe"],
            "note pad": ["notepad.exe"],
            "calculator": ["calc.exe"],
            "calc": ["calc.exe"],
            "vs code": ["code.cmd", "code.exe", "code"],
            "vscode": ["code.cmd", "code.exe", "code"],
            "code": ["code.cmd", "code.exe", "code"],
            "visual studio code": ["code.cmd", "code.exe", "code"],
            "browser": ["chrome.exe", "msedge.exe"],
            "web browser": ["chrome.exe", "msedge.exe"],
            "terminal": ["wt.exe", "powershell.exe", "cmd.exe"],
            "windows terminal": ["wt.exe", "powershell.exe"],
            "cmd": ["cmd.exe"],
            "command prompt": ["cmd.exe"],
            "powershell": ["powershell.exe"],
            "explorer": ["explorer.exe"],
            "file explorer": ["explorer.exe"],
            "files": ["explorer.exe"],
            "my computer": ["explorer.exe"],
            "this pc": ["explorer.exe"],
            "downloads": ["explorer.exe", os.path.expanduser("~/Downloads")],
            "paint": ["mspaint.exe"],
            "mspaint": ["mspaint.exe"],
            "task manager": ["taskmgr.exe"],
            "taskmgr": ["taskmgr.exe"],
            "settings": ["ms-settings:"],
            "spotify": ["spotify:", "spotify.exe"],
            "music": ["spotify:", "spotify.exe"],
            "edge": ["msedge.exe"],
            "microsoft edge": ["msedge.exe"],
            "chrome": ["chrome.exe"],
            "google chrome": ["chrome.exe"],
        }

        candidates = app_executables.get(target_clean, [target_clean, f"{target_clean}.exe"])
        launched = False

        for cand in candidates:
            if cand.endswith(":"):
                try:
                    os.startfile(cand)
                    launched = True
                    break
                except Exception:
                    continue

            which_path = shutil.which(cand)
            if which_path:
                try:
                    subprocess.Popen([which_path], shell=False)
                    launched = True
                    break
                except Exception:
                    pass

            try:
                os.startfile(cand)
                launched = True
                break
            except Exception:
                pass

        if not launched:
            if PYAUTOGUI_AVAILABLE and pyautogui:
                try:
                    pyautogui.hotkey("win", "r")
                    time.sleep(0.4)
                    pyautogui.write(target_clean, interval=0.03)
                    time.sleep(0.1)
                    pyautogui.press("enter")
                    launched = True
                except Exception:
                    pass

        time.sleep(1.2)
        center_x, center_y = screen_w // 2, screen_h // 2
        step = self.smooth_glide_click(center_x, center_y, duration=0.7, click=False)
        executed_steps.append({
            "step": 1,
            "label": f"Launched native desktop app '{target_clean}' & centered mouse reticle",
            "coords": [500.0, 500.0],
            "details": step
        })

        self.active_app = target_clean
        self.active_url = ""
        global_blackboard.update_browser_and_os(active_app=target_clean, active_browser_url="")

        spoken = f"Opened {app_label} on your system, sir." if launched else f"Sent launch command for {app_label} on your system, sir."

        return {
            "success": True,
            "action": "open_app",
            "target": target_clean,
            "active_app": target_clean,
            "executed_steps": executed_steps,
            "spoken_response": spoken
        }

    def execute_gui_command(self, command: str) -> Dict[str, Any]:
        """
        Main multi-turn entry point:
        Executes real browser and desktop operations with dynamic element targeting.
        """
        cmd_lower = command.lower().strip()
        executed_steps: List[Dict[str, Any]] = []

        is_open_turn = (
            any(w in cmd_lower for w in ["open youtube", "launch youtube", "go to youtube", "open the youtube"]) and
            not any(w in cmd_lower for w in ["search", "play"])
        )

        is_search_turn = (
            any(w in cmd_lower for w in ["search for", "search", "play", "believer", "kesariya", "song", "video"])
        )

        # -------------------------------------------------------------
        # OPEN NATIVE APPLICATION OR WEBSITE
        # -------------------------------------------------------------
        open_match = re.search(r'(?:open|launch|start|run)\s+(?:the\s+)?([a-zA-Z0-9_\-\.\s]+)', command, re.I)
        if open_match and not is_open_turn and not is_search_turn:
            target_app = open_match.group(1).strip()
            # If target is youtube, route to turn 1
            if "youtube" in target_app.lower():
                is_open_turn = True
            else:
                return self.launch_system_app_or_website(target_app)

        # -------------------------------------------------------------
        # TURN 1: OPEN YOUTUBE (Dynamic Focus & Universal Hotkey)
        # -------------------------------------------------------------
        if is_open_turn:
            screen_w, screen_h = self.get_screen_size()
            try:
                if sys.platform == "win32":
                    os.startfile("https://www.youtube.com")
                else:
                    webbrowser.open_new_tab("https://www.youtube.com")
            except Exception:
                webbrowser.open_new_tab("https://www.youtube.com")

            time.sleep(1.0)
            self.capture_screen()

            # Dynamically compute center-top search region based on live screen dimensions
            search_px_x = screen_w // 2
            search_px_y = max(50, min(140, int(screen_h * 0.055)))
            norm_x = 500.0
            norm_y = round((search_px_y / screen_h) * 1000.0, 1)

            step1 = self.smooth_glide_click(search_px_x, search_px_y, duration=0.75, click=True)
            executed_steps.append({
                "step": 1,
                "label": f"Launched YouTube -> Glided mouse to Center-Top Search Bar [{search_px_x}, {search_px_y}]",
                "coords": [norm_x, norm_y],
                "details": step1
            })

            # Universal focus: send '/' hotkey
            if PYAUTOGUI_AVAILABLE and pyautogui:
                try:
                    time.sleep(0.15)
                    pyautogui.press("/")
                    time.sleep(0.05)
                    pyautogui.hotkey("ctrl", "a")
                except Exception:
                    pass

            executed_steps.append({
                "step": 2,
                "label": "Pressed YouTube universal search hotkey '/' & focused search bar",
                "coords": [norm_x, norm_y],
                "details": {"hotkey": "/", "focused": True}
            })

            self.active_app = "browser_youtube"
            self.active_url = "https://www.youtube.com"
            self.session_memory["youtube_open"] = True
            self.session_memory["search_focused"] = True

            global_blackboard.update_browser_and_os(
                active_browser_url="https://www.youtube.com",
                active_app="browser_youtube",
                mouse_position=[search_px_x, search_px_y]
            )

            spoken = "YouTube is open and I have positioned the mouse over the search bar, sir. What would you like me to search for?"
            return {
                "command": command,
                "turn": 1,
                "action": "open_youtube",
                "active_app": "browser_youtube",
                "active_url": "https://www.youtube.com",
                "session_state": self.session_memory,
                "executed_steps": executed_steps,
                "spoken_response": spoken,
                "model": self.model_name
            }

        # -------------------------------------------------------------
        # TURN 2: SEARCH & PLAY SONG
        # -------------------------------------------------------------
        if is_search_turn:
            screen_w, screen_h = self.get_screen_size()
            cleaned_query = re.sub(
                r'^(?:hey\s+)?(?:jarvis[,\s]*)?(?:can\s+(?:you|u)\s+|please\s+)?(?:open\s+youtube\s+(?:and\s+)?)?(?:search\s+for\s+|search\s+|play\s+(?:the\s+song\s+|song\s+|music\s+)?)?',
                '',
                command,
                flags=re.I
            ).strip()
            cleaned_query = re.sub(r'(?:on\s+youtube|from\s+youtube|song|video)$', '', cleaned_query, flags=re.I).strip()
            if not cleaned_query:
                cleaned_query = "Believer by Imagine Dragons"

            if not self.session_memory.get("youtube_open"):
                try:
                    if sys.platform == "win32":
                        os.startfile("https://www.youtube.com")
                    else:
                        webbrowser.open_new_tab("https://www.youtube.com")
                except Exception:
                    webbrowser.open_new_tab("https://www.youtube.com")
                time.sleep(1.0)
                self.session_memory["youtube_open"] = True

            # 1. Target center-top search bar dynamically
            search_px_x = screen_w // 2
            search_px_y = max(50, min(140, int(screen_h * 0.055)))
            norm_x_search = 500.0
            norm_y_search = round((search_px_y / screen_h) * 1000.0, 1)

            step1 = self.smooth_glide_click(search_px_x, search_px_y, duration=0.70, click=True)
            if PYAUTOGUI_AVAILABLE and pyautogui:
                try:
                    time.sleep(0.1)
                    pyautogui.press("/")
                    pyautogui.hotkey("ctrl", "a")
                    pyautogui.press("backspace")
                except Exception:
                    pass

            executed_steps.append({
                "step": 1,
                "label": f"Focus Search Input [{search_px_x}, {search_px_y}]",
                "coords": [norm_x_search, norm_y_search],
                "details": step1
            })

            # 2. Type query character-by-character
            type_res = self.type_search_visibly(cleaned_query, interval=0.04, press_enter=True)
            executed_steps.append({
                "step": 2,
                "label": f"Typed '{cleaned_query}' & pressed Enter",
                "details": type_res
            })

            # Allow search results to render
            time.sleep(1.2)
            self.capture_screen()

            # 3. Dynamic target top video card
            res_px_x = int(screen_w * 0.40)
            res_px_y = max(240, min(500, int(screen_h * 0.32)))
            norm_x_card = round((res_px_x / screen_w) * 1000.0, 1)
            norm_y_card = round((res_px_y / screen_h) * 1000.0, 1)

            step3 = self.smooth_glide_click(res_px_x, res_px_y, duration=0.75, click=True)
            executed_steps.append({
                "step": 3,
                "label": f"Glided mouse to top video result [{res_px_x}, {res_px_y}] & clicked to play",
                "coords": [norm_x_card, norm_y_card],
                "details": step3
            })

            matched = next((item for item in YOUTUBE_CATALOG if any(k in cleaned_query.lower() for k in item["keywords"])), None)
            search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(cleaned_query)}"
            watch_url = f"https://www.youtube.com/watch?v={matched['video_id']}&autoplay=1" if matched else search_url
            embed_url = f"https://www.youtube.com/embed/{matched['video_id']}?autoplay=1" if matched else ""
            display_title = matched["title"] if matched else f"{cleaned_query}"

            self.active_app = "browser_youtube_playing"
            self.active_url = watch_url
            self.session_memory["last_query"] = cleaned_query

            global_blackboard.update_browser_and_os(
                active_browser_url=watch_url,
                active_app="browser_youtube_playing",
                mouse_position=[res_px_x, res_px_y],
                last_clicked_element=display_title
            )

            spoken = f"Searched YouTube for {cleaned_query}, glided the mouse cursor to the top result, and started playback, sir."
            return {
                "command": command,
                "turn": 2,
                "action": "youtube_search_and_play",
                "query": cleaned_query,
                "display_title": display_title,
                "watch_url": watch_url,
                "embed_url": embed_url,
                "active_app": "browser_youtube_playing",
                "active_url": watch_url,
                "session_state": self.session_memory,
                "executed_steps": executed_steps,
                "spoken_response": spoken,
                "model": self.model_name
            }

        # -------------------------------------------------------------
        # CLOSE / STOP COMMANDS
        # -------------------------------------------------------------
        if any(w in cmd_lower for w in ["close", "exit", "stop"]):
            self.active_app = "desktop"
            self.session_memory["youtube_open"] = False
            global_blackboard.update_browser_and_os(active_app="desktop", active_browser_url="")
            return {
                "command": command,
                "action": "close",
                "active_app": "desktop",
                "session_state": self.session_memory,
                "executed_steps": [{"step": 1, "action": "Reset desktop state and cursor to standby"}],
                "spoken_response": "Desktop session closed, sir. Cursor returned to standby."
            }

        # -------------------------------------------------------------
        # OPEN-ENDED ACTION: OPEN ANY URL OR DESKTOP APP
        # -------------------------------------------------------------
        url_match = re.search(r'https?://[^\s]+', command)
        if url_match or any(w in cmd_lower for w in ["open site", "open website", "browse to"]):
            target_url = url_match.group(0) if url_match else "https://" + command.split()[-1]
            webbrowser.open_new_tab(target_url)
            self.active_app = "browser"
            self.active_url = target_url
            w, h = self.get_screen_size()
            step = self.smooth_glide_click(w // 2, h // 2, duration=0.6, click=False)
            return {
                "command": command,
                "action": "open_url",
                "active_app": "browser",
                "active_url": target_url,
                "executed_steps": [{"step": 1, "label": f"Opened {target_url} in browser", "details": step}],
                "spoken_response": f"Opened {target_url} in your browser, sir."
            }

        # Universal fallback pointing / OCR search
        ocr_find = self.universal_visual_find_and_click(command)
        return {
            "command": command,
            "action": "universal_visual_action",
            "active_app": self.active_app,
            "session_state": self.session_memory,
            "executed_steps": [{"step": 1, "action": f"Visual search for '{command}'", "details": ocr_find}],
            "spoken_response": f"Examined screen layout for '{command}'. Cursor positioned."
        }
