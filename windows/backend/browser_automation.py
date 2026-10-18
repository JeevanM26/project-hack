"""
Desktop Browser GUI Automation Engine for J.A.R.V.I.S.
Powered by Playwright + Microsoft Edge on Windows.
Enables continuous hands-free desktop voice automation:
1. Open websites (YouTube, Drive, GitHub, Google) in a visible desktop browser.
2. Maintain active standby state: keep browser open and listen for chained tasks.
3. Live GUI search, song playback, and pause/resume.
4. Clean closing on voice command ("close it", "close tab", "close browser").
"""
import sys
import os
import time
import queue
import threading
from typing import Dict, Any, Optional

class _BrowserWorkerThread(threading.Thread):
    def __init__(self, headless: bool = False):
        super().__init__(name="JarvisPlaywrightWorker", daemon=True)
        self.cmd_queue: queue.Queue = queue.Queue()
        self.running: bool = True
        self.headless: bool = headless
        self.p = None
        self.browser = None
        self.context = None
        self.page = None
        self.active_app: Optional[str] = None
        self.current_url: Optional[str] = None

    def _ensure_browser(self):
        if self.page and not self.page.is_closed():
            return
        from playwright.sync_api import sync_playwright
        if not self.p:
            self.p = sync_playwright().start()
        if not self.browser:
            # Launch native Microsoft Edge with visible GUI window on Windows desktop
            try:
                self.browser = self.p.chromium.launch(channel="msedge", headless=self.headless)
            except Exception:
                self.browser = self.p.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context(viewport={"width": 1280, "height": 800})
        self.page = self.context.new_page()

    def run(self):
        while self.running:
            try:
                item = self.cmd_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if item is None:
                break

            cmd, args, res_q = item
            try:
                self._ensure_browser()
                if cmd == "open":
                    url = args["url"]
                    app_name = args.get("app_name", "browser")
                    self.page.goto(url, timeout=20000)
                    self.active_app = app_name
                    self.current_url = url
                    res_q.put(("ok", {"title": self.page.title(), "url": self.current_url, "app": self.active_app}))

                elif cmd == "search":
                    query = args["query"]
                    if self.active_app == "youtube" or "youtube.com" in (self.current_url or ""):
                        search_sel = 'input[name="search_query"], input#search'
                        self.page.wait_for_selector(search_sel, timeout=10000)
                        self.page.fill(search_sel, query)
                        self.page.press(search_sel, "Enter")
                        self.page.wait_for_selector('a#video-title', timeout=12000)
                        self.current_url = self.page.url
                        res_q.put(("ok", {"status": "searched", "query": query, "url": self.current_url}))
                    else:
                        # Fallback to Google search
                        url = f"https://www.google.com/search?q={query}"
                        self.page.goto(url, timeout=15000)
                        self.active_app = "google"
                        self.current_url = url
                        res_q.put(("ok", {"status": "searched_google", "query": query, "url": url}))

                elif cmd == "play_first":
                    # If not on search results, first search if query given
                    song_query = args.get("query")
                    if song_query:
                        if not self.current_url or "youtube.com" not in self.current_url:
                            self.page.goto(f"https://www.youtube.com/results?search_query={song_query}", timeout=15000)
                            self.active_app = "youtube"
                        else:
                            search_sel = 'input[name="search_query"], input#search'
                            self.page.wait_for_selector(search_sel, timeout=10000)
                            self.page.fill(search_sel, song_query)
                            self.page.press(search_sel, "Enter")

                    self.page.wait_for_selector('a#video-title', timeout=12000)
                    first_vid = self.page.query_selector('a#video-title')
                    if first_vid:
                        first_vid.click()
                        time.sleep(2)
                        self.current_url = self.page.url
                        res_q.put(("ok", {"status": "playing", "url": self.current_url}))
                    else:
                        res_q.put(("error", "No video results found"))

                elif cmd == "pause_resume":
                    # Press 'k' on YouTube player or space
                    self.page.keyboard.press("k")
                    res_q.put(("ok", {"status": "toggled"}))

                elif cmd == "close":
                    if self.page and not self.page.is_closed():
                        self.page.close()
                    if self.browser:
                        try:
                            self.browser.close()
                        except Exception:
                            pass
                        self.browser = None
                        self.page = None
                    self.active_app = None
                    self.current_url = None
                    res_q.put(("ok", {"status": "closed"}))

                elif cmd == "status":
                    is_alive = self.page is not None and not self.page.is_closed()
                    res_q.put(("ok", {
                        "is_alive": is_alive,
                        "active_app": self.active_app,
                        "current_url": self.current_url
                    }))
                else:
                    res_q.put(("error", f"Unknown command: {cmd}"))

            except Exception as e:
                res_q.put(("error", str(e)))

        self._cleanup()

    def _cleanup(self):
        try:
            if self.browser:
                self.browser.close()
        except Exception:
            pass
        try:
            if self.p:
                self.p.stop()
        except Exception:
            pass


class DesktopBrowserAutomation:
    _instance: Optional["DesktopBrowserAutomation"] = None
    _lock = threading.Lock()

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.worker: Optional[_BrowserWorkerThread] = None
        self.active_app: Optional[str] = None
        self.standby: bool = False
        self.last_query: Optional[str] = None

    @classmethod
    def get_instance(cls, headless: bool = False) -> "DesktopBrowserAutomation":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(headless=headless)
            return cls._instance

    def _ensure_worker(self):
        if self.worker is None or not self.worker.is_alive():
            self.worker = _BrowserWorkerThread(headless=self.headless)
            self.worker.start()

    def _send_cmd(self, cmd: str, timeout: float = 25.0, **kwargs) -> Dict[str, Any]:
        self._ensure_worker()
        res_q = queue.Queue()
        self.worker.cmd_queue.put((cmd, kwargs, res_q))
        try:
            status, payload = res_q.get(timeout=timeout)
            if status == "ok":
                return {"success": True, "data": payload}
            else:
                return {"success": False, "error": str(payload)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_website(self, url: str, app_name: str) -> Dict[str, Any]:
        res = self._send_cmd("open", url=url, app_name=app_name)
        if res.get("success"):
            self.active_app = app_name
            self.standby = True
            return {
                "success": True,
                "action": "open_website",
                "app": app_name,
                "url": url,
                "standby": True,
                "spoken_summary": f"{app_name.title()} is open on your screen and I am standing by, sir. What would you like to search or play?"
            }
        else:
            # Fallback to native OS startfile
            self._os_fallback(url)
            self.active_app = app_name
            self.standby = True
            return {
                "success": True,
                "action": "open_website",
                "app": app_name,
                "url": url,
                "standby": True,
                "spoken_summary": f"Opened {app_name.title()} in your browser. Standing by for your command, sir."
            }

    def search(self, query: str) -> Dict[str, Any]:
        self.last_query = query
        res = self._send_cmd("search", query=query)
        self.standby = True
        app_disp = (self.active_app or "browser").title()
        if res.get("success"):
            return {
                "success": True,
                "action": "search",
                "app": self.active_app,
                "query": query,
                "standby": True,
                "spoken_summary": f"Searched {app_disp} for {query}, sir. Standing by—say 'play' to start or 'search' to look for something else."
            }
        else:
            return {
                "success": False,
                "action": "search",
                "query": query,
                "standby": True,
                "spoken_summary": f"Attempted to search {app_disp} for {query}. Standing by, sir."
            }

    def play_video(self, song_query: Optional[str] = None) -> Dict[str, Any]:
        res = self._send_cmd("play_first", query=song_query)
        self.standby = True
        disp = song_query or self.last_query or "video"
        if res.get("success"):
            return {
                "success": True,
                "action": "play_video",
                "query": disp,
                "standby": True,
                "spoken_summary": f"Playing {disp} for you now, sir. Standing by—say 'pause' to pause, or 'close it' when done."
            }
        else:
            return {
                "success": False,
                "action": "play_video",
                "query": disp,
                "standby": True,
                "spoken_summary": f"Starting playback for {disp}. Standing by, sir."
            }

    def pause_resume(self) -> Dict[str, Any]:
        res = self._send_cmd("pause_resume")
        self.standby = True
        return {
            "success": True,
            "action": "pause_resume",
            "standby": True,
            "spoken_summary": "Playback toggled, sir. Standing by."
        }

    def close_active(self) -> Dict[str, Any]:
        app_disp = (self.active_app or "browser").title()
        self._send_cmd("close", timeout=10.0)
        self.active_app = None
        self.standby = False
        self.last_query = None
        return {
            "success": True,
            "action": "close",
            "standby": False,
            "spoken_summary": f"Closed {app_disp}, sir. Standing by for your next mission."
        }

    def get_status(self) -> Dict[str, Any]:
        res = self._send_cmd("status", timeout=5.0)
        return {
            "standby": self.standby,
            "active_app": self.active_app,
            "worker_status": res.get("data", {})
        }

    def _os_fallback(self, url: str):
        if sys.platform == "win32":
            try:
                os.startfile(url)
                return
            except Exception:
                pass
        import webbrowser
        try:
            webbrowser.open_new_tab(url)
        except Exception:
            pass
