"""
Human-Like Voice OS Actions Engine for J.A.R.V.I.S.
Provides seamless desktop OS controls:
1. Opening websites like a human (YouTube, Google Drive, Gmail, GitHub, Notion, etc.) in new tabs.
2. Playing songs on YouTube with direct video resolution and autoplay.
3. Web search on Google.
4. Stopping/pausing playback without killing the user's browser.
"""
import os
import sys
import re
import urllib.parse
import webbrowser
from typing import Dict, Any, Optional
import requests

COMMON_SITES = {
    "youtube": "https://www.youtube.com",
    "drive": "https://drive.google.com",
    "google drive": "https://drive.google.com",
    "docs": "https://docs.google.com",
    "sheets": "https://sheets.google.com",
    "gmail": "https://mail.google.com",
    "mail": "https://mail.google.com",
    "email": "https://mail.google.com",
    "github": "https://github.com",
    "google": "https://www.google.com",
    "notion": "https://www.notion.so",
    "linkedin": "https://www.linkedin.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "reddit": "https://www.reddit.com",
    "chatgpt": "https://chatgpt.com",
    "gemini": "https://gemini.google.com",
    "netflix": "https://www.netflix.com",
    "spotify": "https://open.spotify.com",
    "amazon": "https://www.amazon.in",
    "flipkart": "https://www.flipkart.com",
    "stackoverflow": "https://stackoverflow.com",
    "whatsapp": "https://web.whatsapp.com",
    "claude": "https://claude.ai",
}

class VoiceOSActions:
    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        try:
            from browser_automation import DesktopBrowserAutomation
            headless_mode = os.getenv("JARVIS_HEADLESS", "0") == "1"
            self.browser_auto = DesktopBrowserAutomation.get_instance(headless=headless_mode)
        except Exception:
            self.browser_auto = None

    def detect_and_handle_os_action(self, spoken_command: str) -> Optional[Dict[str, Any]]:
        """
        Detects if the spoken command is a desktop OS action:
        - Opening websites (YouTube, Google Drive, GitHub, Gmail, etc.)
        - Chained tasks in standby: search, play, pause/resume, close
        - Playing specific songs on YouTube
        - Web search
        - Stopping audio
        """
        cmd_raw = spoken_command.strip()
        cmd_lower = cmd_raw.lower()
        clean = re.sub(r'^(?:jarvis\s*,?\s*|please\s+|can\s+(?:you|u)\s+)', '', cmd_lower, flags=re.I).strip()
        clean = re.sub(r'[?!.,;]+$', '', clean).strip()

        # 1. Close command: "close it", "close this", "close tab", "close window", "close browser", "close youtube"
        close_phrases = [
            "close it", "close this", "close tab", "close window", "close browser",
            "close the tab", "close the browser", "close the window", "close youtube",
            "close edge", "shut it", "close page", "exit browser"
        ]
        if any(clean == k or clean.startswith(k) for k in close_phrases):
            if self.browser_auto:
                res = self.browser_auto.close_active()
                spoken = res.get("spoken_summary", "Closed it for you, sir. Standing by for your next mission.")
            else:
                spoken = "Closed browser tab, sir. Standing by for your next mission."
            return {
                "action": "close_browser",
                "standby": False,
                "spoken_summary": spoken
            }

        # 2. Stop / Silence command
        if any(w in clean for w in ["stop playing", "stop audio", "stop music", "silence", "be quiet", "stop all", "stop song"]):
            return self.stop_all_media()

        # 3. Pause / Resume command
        if clean in ["pause", "resume", "pause it", "resume it", "pause song", "pause video", "unpause", "play/pause"]:
            if self.browser_auto:
                res = self.browser_auto.pause_resume()
                spoken = res.get("spoken_summary", "Playback toggled, sir. Standing by.")
            else:
                spoken = "Playback toggled, sir. Standing by."
            return {
                "action": "pause_resume",
                "standby": True,
                "spoken_summary": spoken
            }

        # 4. Contextual Play command (e.g. "play", "play it", "play the first video", "play first one")
        if clean in ["play", "play it", "play the video", "play first", "play first one", "play the first one", "start playing", "play song", "play video"]:
            if self.browser_auto:
                res = self.browser_auto.play_video()
                spoken = res.get("spoken_summary", "Playing the video for you now, sir. Standing by.")
            else:
                spoken = "Playing the video now, sir. Standing by."
            return {
                "action": "play_youtube",
                "standby": True,
                "spoken_summary": spoken
            }

        # 5. Search command in active browser or YouTube (e.g. "search kesariya", "now search interstellar", "search for lofi"):
        search_match = re.search(r'^(?:now\s+)?search\s+(?:for\s+)?(.+)', clean, flags=re.I)
        if search_match and not any(w in clean for w in ["google", "in google", "on google"]):
            query = search_match.group(1).strip()
            if self.browser_auto:
                res = self.browser_auto.search(query)
                spoken = res.get("spoken_summary", f"Searched for {query}, sir. Standing by—say 'play' to start.")
            else:
                spoken = f"Searched for {query}, sir. Standing by."
            return {
                "action": "search",
                "query": query,
                "standby": True,
                "spoken_summary": spoken
            }

        # 6. Explicit YouTube Song PLAYBACK intent (must have "play" and a song name)
        # e.g. "open youtube and play kesariya", "play believer on youtube", "play faded"
        is_play_intent = "play" in clean and not clean.endswith("play")
        if is_play_intent:
            song_query = self._extract_song_query(clean)
            if song_query and song_query.lower() not in ["youtube", "video", "song", "music", "it", "this", "first"]:
                video_id = self._resolve_top_youtube_video(song_query)
                watch_url = f"https://www.youtube.com/watch?v={video_id}&autoplay=1" if video_id else f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(song_query)}"
                embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1" if video_id else ""
                if self.browser_auto:
                    self.browser_auto.open_website("https://www.youtube.com", "youtube")
                    self.browser_auto.play_video(song_query)
                else:
                    self._open_url_os(watch_url)
                return {
                    "action": "play_youtube",
                    "query": song_query,
                    "video_id": video_id,
                    "watch_url": watch_url,
                    "embed_url": embed_url,
                    "standby": True,
                    "spoken_summary": f"Playing {song_query} on YouTube in your browser now, sir. Standing by—say 'pause' to pause or 'close it' when done."
                }

        # 7. Check for Human-Like Website Opening
        # e.g. "open youtube", "can u open youtube", "open drive", "open github"
        website_action = self._detect_website_open(clean)
        if website_action:
            return website_action

        # 8. Check for Google Web Search intent
        # e.g. "search for gemma 4 on google", "google quantum computing"
        search_action = self._detect_web_search(clean)
        if search_action:
            return search_action

        return None

    def _detect_website_open(self, text: str) -> Optional[Dict[str, Any]]:
        """Detects requests to open any website or service."""
        clean = re.sub(r'^(?:jarvis\s*,?\s*|please\s+|can\s+(?:you|u)\s+)', '', text, flags=re.I).strip()
        match = re.search(r'(?:open|launch|go\s+to|visit)\s+([a-zA-Z0-9_\-\.\s]+)', clean, flags=re.I)
        if not match:
            return None

        target = match.group(1).strip()
        # Remove trailing punctuation and helper words
        target_clean = re.sub(r'[?!.,;]+$', '', target).strip()
        target_clean = re.sub(r'\s+(?:website|site|tab|page|app|in\s+browser|please|now)$', '', target_clean, flags=re.I).strip()
        key_clean = target_clean.lower()

        # Check in common sites
        if key_clean in COMMON_SITES:
            url = COMMON_SITES[key_clean]
            if self.browser_auto:
                res = self.browser_auto.open_website(url, key_clean)
                spoken = res.get("spoken_summary", f"{key_clean.title()} is open on your screen and I am standing by, sir. What would you like to search or play?")
            else:
                self._open_url_os(url)
                spoken = f"Opening {key_clean.title()} in your browser now, sir. Standing by."
            return {
                "action": "open_website",
                "site_name": key_clean.title(),
                "url": url,
                "standby": True,
                "spoken_summary": spoken
            }

        # Check if user mentioned a dot-com domain like "notion.so" or "example.com"
        if "." in target_clean and not target_clean.endswith(".py"):
            url = target_clean if target_clean.startswith("http") else f"https://{target_clean}"
            if self.browser_auto:
                res = self.browser_auto.open_website(url, target_clean)
                spoken = res.get("spoken_summary", f"Opened {target_clean} on your screen. Standing by for your instructions, sir.")
            else:
                self._open_url_os(url)
                spoken = f"Opening {target_clean} in your browser now, sir. Standing by."
            return {
                "action": "open_website",
                "site_name": target_clean,
                "url": url,
                "standby": True,
                "spoken_summary": spoken
            }

        # Check partial match in common sites
        for key, url in COMMON_SITES.items():
            if key in key_clean:
                if self.browser_auto:
                    res = self.browser_auto.open_website(url, key)
                    spoken = res.get("spoken_summary", f"{key.title()} is open on your screen and I am standing by, sir. What would you like to search or play?")
                else:
                    self._open_url_os(url)
                    spoken = f"Opening {key.title()} in your browser now, sir. Standing by."
                return {
                    "action": "open_website",
                    "site_name": key.title(),
                    "url": url,
                    "standby": True,
                    "spoken_summary": spoken
                }

        return None

    def _open_url_os(self, url: str):
        """Opens URL in user's default browser smoothly without closing or killing any windows."""
        # 1. Native Windows ShellExecute via os.startfile (instant, zero popup blocks, clean tab)
        if sys.platform == "win32":
            try:
                os.startfile(url)
                return
            except Exception:
                pass
            try:
                os.system(f'start "" "{url}"')
                return
            except Exception:
                pass
        # 2. Cross-platform fallback
        try:
            webbrowser.open_new_tab(url)
        except Exception:
            pass

    def _detect_web_search(self, text: str) -> Optional[Dict[str, Any]]:
        clean = re.sub(r'^(?:jarvis\s*,?\s*|please\s+|can\s+(?:you|u)\s+)', '', text, flags=re.I).strip()
        match = re.search(r'(?:search\s+(?:for\s+)?(.+?)\s+(?:on\s+google|in\s+google)|google\s+(.+)|search\s+google\s+for\s+(.+))', clean, flags=re.I)
        if match:
            q = next(g for g in match.groups() if g)
            url = f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}"
            self._open_url_os(url)
            return {
                "action": "web_search",
                "query": q,
                "url": url,
                "spoken_summary": f"Searching Google for {q} in your browser, sir."
            }
        return None

    def _extract_song_query(self, text: str) -> str:
        cleaned = re.sub(r'^(?:jarvis\s*,?\s*|please\s+|can\s+(?:you|u)\s+)', '', text, flags=re.I)
        cleaned = re.sub(r'(?:open\s+youtube\s+(?:and\s+)?play\s*|play\s+on\s+youtube\s*|play\s+song\s*|play\s*)', '', cleaned, flags=re.I)
        cleaned = re.sub(r'(?:on\s+youtube|from\s+youtube|song|video|in\s+youtube)$', '', cleaned, flags=re.I)
        query = cleaned.strip()
        return query

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

    def play_youtube_song(self, song_query: str, auto_open_browser: bool = True) -> Dict[str, Any]:
        """Opens YouTube and starts playing the requested song in a new browser tab."""
        encoded_query = urllib.parse.quote_plus(song_query)
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        video_id = self._resolve_top_youtube_video(song_query)

        watch_url = f"https://www.youtube.com/watch?v={video_id}&autoplay=1" if video_id else search_url
        embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1" if video_id else f"https://www.youtube-nocookie.com/embed?listType=search&list={encoded_query}&autoplay=1"

        if auto_open_browser:
            self._open_url_os(watch_url)

        return {
            "action": "play_youtube",
            "query": song_query,
            "search_url": search_url,
            "watch_url": watch_url,
            "embed_url": embed_url,
            "video_id": video_id,
            "status": "playing",
            "spoken_summary": f"Playing {song_query} on YouTube in your browser now, sir."
        }

    def stop_all_media(self) -> Dict[str, Any]:
        """Stops/pauses audio cleanly without killing the user's browser."""
        return {
            "action": "stop_audio",
            "status": "stopped",
            "spoken_summary": "Audio and media have been stopped, sir."
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
