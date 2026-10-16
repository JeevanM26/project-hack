"""
Voice OS Actions Engine for J.A.R.V.I.S.
Handles desktop actions like opening YouTube to play songs, launching external tools,
and scaffolding full multi-file projects on disk.
"""
import os
import re
import urllib.parse
import webbrowser
from typing import Dict, Any, Optional

class VoiceOSActions:
    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def detect_and_handle_os_action(self, spoken_command: str) -> Optional[Dict[str, Any]]:
        """
        Detects if the spoken command is an OS action (e.g. play a song on YouTube,
        open a browser URL, or scaffold a project) and executes it.
        """
        cmd_lower = spoken_command.lower().strip()

        # Check for YouTube song playback intent
        # Examples: "open youtube and play kesariya", "play despacito on youtube", "jarvis play believer"
        youtube_match = re.search(r'(?:open\s+youtube\s+(?:and\s+)?play|play\s+(.+?)\s+on\s+youtube|play\s+song\s+(.+?)|play\s+(.+?)\s+song|open\s+youtube\s+for\s+(.+))', cmd_lower)
        
        if "youtube" in cmd_lower or ("play" in cmd_lower and any(w in cmd_lower for w in ["song", "music", "track", "video"])):
            song_query = self._extract_song_query(cmd_lower)
            return self.play_youtube_song(song_query)

        return None

    def _extract_song_query(self, text: str) -> str:
        # Strip common prefixes
        cleaned = re.sub(r'^(?:jarvis\s*,?\s*|please\s+|can\s+you\s+)', '', text, flags=re.I)
        cleaned = re.sub(r'(?:open\s+youtube\s+(?:and\s+)?play\s*|play\s+on\s+youtube\s*|play\s+song\s*|play\s*)', '', cleaned, flags=re.I)
        cleaned = re.sub(r'(?:on\s+youtube|from\s+youtube|song|video)$', '', cleaned, flags=re.I)
        query = cleaned.strip()
        return query or "Kesariya Brahmastra"

    def play_youtube_song(self, song_query: str, auto_open_browser: bool = False) -> Dict[str, Any]:
        """
        Prepares YouTube playback data for both the frontend embedded dock
        and optional local system browser launch.
        """
        encoded_query = urllib.parse.quote_plus(song_query)
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        # Curated top popular tracks map for instantaneous embedded iframe playback
        embed_lookup = {
            "kesariya": "BddP6PYo2gs",
            "believer": "7wtfhZwyrcc",
            "shape of you": "JGwWNGJdvx8",
            "faded": "60ItHLz5WEA",
            "despacito": "kJQP7kiw5Fk",
            "interstellar": "UDVtMYqUAyw",
            "starboy": "34Na4j8AVgA",
            "jai ho": "Yc_8_5YqR7E",
        }
        
        video_id = None
        for key, vid in embed_lookup.items():
            if key in song_query.lower():
                video_id = vid
                break
        
        # Default fallback embed uses YouTube search / embed player
        embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1" if video_id else f"https://www.youtube-nocookie.com/embed?listType=search&list={encoded_query}&autoplay=1"

        if auto_open_browser:
            try:
                target_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else search_url
                webbrowser.open(target_url)
            except Exception:
                pass

        return {
            "action": "open_youtube",
            "query": song_query,
            "search_url": search_url,
            "embed_url": embed_url,
            "video_id": video_id,
            "status": "ready",
            "spoken_summary": f"Opening YouTube and playing {song_query} right now, sir."
        }

    def write_scaffolded_project(self, project_name: str, files_dict: Dict[str, str]) -> Dict[str, Any]:
        """
        Writes a newly generated multi-file project to disk in the projects folder.
        """
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
