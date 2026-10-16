"""
Voice OS Actions Engine for J.A.R.V.I.S.
Handles desktop actions like opening YouTube to play songs with real GUI automation,
stopping background audio/browsers, and scaffolding full multi-file projects on disk.
"""
import os
import re
import sys
import time
import subprocess
import threading
import urllib.parse
import webbrowser
from typing import Dict, Any, Optional
import requests

class VoiceOSActions:
    _lock = threading.Lock()
    _active_p = None
    _active_browser = None

    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def detect_and_handle_os_action(self, spoken_command: str) -> Optional[Dict[str, Any]]:
        """
        Detects if the spoken command is an OS action (e.g. play a song on YouTube,
        stop audio/media, or scaffold a project) and executes it.
        """
        cmd_lower = spoken_command.lower().strip()

        # Check for stop / silence media commands
        if any(w in cmd_lower for w in ["stop playing", "stop audio", "stop music", "silence", "be quiet", "pause audio", "stop all"]):
            return self.stop_all_media()

        # Check for YouTube song playback intent
        if "youtube" in cmd_lower or ("play" in cmd_lower and any(w in cmd_lower for w in ["song", "music", "track", "video"])):
            song_query = self._extract_song_query(cmd_lower)
            return self.play_youtube_song(song_query, auto_open_browser=True)

        return None

    def stop_all_media(self) -> Dict[str, Any]:
        """Terminates any active automated browser processes and silences background audio."""
        with VoiceOSActions._lock:
            try:
                if VoiceOSActions._active_browser:
                    VoiceOSActions._active_browser.close()
            except Exception:
                pass
            VoiceOSActions._active_browser = None
            VoiceOSActions._active_p = None

            # Force kill background automated Edge/Chrome instances if needed
            try:
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/IM", "msedge.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

        return {
            "action": "stop_audio",
            "status": "stopped",
            "spoken_summary": "All background audio and browser media have been stopped immediately, sir."
        }

    def _extract_song_query(self, text: str) -> str:
        cleaned = re.sub(r'^(?:jarvis\s*,?\s*|please\s+|can\s+you\s+)', '', text, flags=re.I)
        cleaned = re.sub(r'(?:open\s+youtube\s+(?:and\s+)?play\s*|play\s+on\s+youtube\s*|play\s+song\s*|play\s*)', '', cleaned, flags=re.I)
        cleaned = re.sub(r'(?:on\s+youtube|from\s+youtube|song|video)$', '', cleaned, flags=re.I)
        query = cleaned.strip()
        return query or "Kesariya Brahmastra"

    def _resolve_top_youtube_video(self, song_query: str) -> Optional[str]:
        known = {
            "kesariya": "BddP6PYo2gs",
            "believer": "7wtfhZwyrcc",
            "shape of you": "JGwWNGJdvx8",
            "faded": "60ItHLz5WEA",
            "despacito": "kJQP7kiw5Fk",
            "interstellar": "UDVtMYqUAyw",
            "starboy": "34Na4j8AVgA",
            "jai ho": "Yc_8_5YqR7E",
        }
        for k, vid in known.items():
            if k in song_query.lower():
                return vid

        try:
            encoded = urllib.parse.quote_plus(song_query)
            res = requests.get(
                f"https://www.youtube.com/results?search_query={encoded}",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
                timeout=4
            ).text
            vids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', res)
            if vids:
                return vids[0]
        except Exception:
            pass
        return None

    def _launch_gui_youtube_workflow(self, song_query: str, watch_url: str, search_url: str):
        """
        GUI Automation: Launches single visible browser window, navigates to YouTube,
        enters the search query, and plays the video. Prevents multiple instances.
        """
        # Always terminate previous instance first
        self.stop_all_media()

        try:
            from playwright.sync_api import sync_playwright
            with VoiceOSActions._lock:
                p = sync_playwright().start()
                VoiceOSActions._active_p = p
                browser = p.chromium.launch(channel="msedge", headless=False)
                VoiceOSActions._active_browser = browser

            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()
            page.goto("https://www.youtube.com", timeout=20000)
            time.sleep(1)

            search_box = page.wait_for_selector('input[name="search_query"], input#search', timeout=10000)
            if search_box:
                search_box.fill(song_query)
                search_box.press("Enter")

            top_vid = page.wait_for_selector('a#video-title', timeout=12000)
            if top_vid:
                top_vid.click()

            # Keep playing until closed
            page.wait_for_timeout(7200000)
        except Exception as e:
            print(f"[VoiceOSActions GUI Browser Fallback]: {e}")
            try:
                webbrowser.open(watch_url or search_url, new=2)
            except Exception:
                pass

    def play_youtube_song(self, song_query: str, auto_open_browser: bool = True) -> Dict[str, Any]:
        """
        Executes local GUI automation: opens single browser instance, searches YouTube, and plays the song.
        """
        encoded_query = urllib.parse.quote_plus(song_query)
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        video_id = self._resolve_top_youtube_video(song_query)

        watch_url = f"https://www.youtube.com/watch?v={video_id}&autoplay=1" if video_id else search_url
        embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1" if video_id else f"https://www.youtube-nocookie.com/embed?listType=search&list={encoded_query}&autoplay=1"

        if auto_open_browser:
            threading.Thread(
                target=self._launch_gui_youtube_workflow,
                args=(song_query, watch_url, search_url),
                daemon=True
            ).start()

        return {
            "action": "open_youtube",
            "query": song_query,
            "search_url": search_url,
            "watch_url": watch_url,
            "embed_url": embed_url,
            "video_id": video_id,
            "status": "launched_gui_automation",
            "spoken_summary": f"Opening your browser locally, navigating to YouTube, searching for {song_query}, and starting playback now, sir."
        }

    def write_scaffolded_project(self, project_name: str, files_dict: Dict[str, str]) -> Dict[str, Any]:
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', project_name)
        target_dir = os.path.join(self.workspace_root, "generated_projects", safe_name)
        os.makedirs(target_dir, exist_ok=True)

        written_files = []
        for filename, content in files_dict.items():
            file_path = os.path.join(target_dir, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            written_files.append({"filename": filename, "path": file_path, "size": len(content)})

        return {
            "project_name": safe_name,
            "target_dir": target_dir,
            "files_created": written_files,
            "count": len(written_files)
        }
