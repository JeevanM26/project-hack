import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from os_actions import VoiceOSActions

def test_detect_youtube_playback_intent():
    os_engine = VoiceOSActions()
    
    cmd = "Jarvis, open YouTube and play Kesariya"
    res = os_engine.detect_and_handle_os_action(cmd)
    
    assert res is not None
    assert res["action"] == "open_youtube"
    assert "kesariya" in res["query"].lower()
    assert res["video_id"] == "BddP6PYo2gs"
    assert "embed" in res["embed_url"]

def test_detect_non_os_command():
    os_engine = VoiceOSActions()
    res = os_engine.detect_and_handle_os_action("Jarvis, scan payment_service.py AST for security bugs")
    assert res is None
