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
    assert res["action"] == "play_youtube"
    assert "kesariya" in res["query"].lower()
    assert res["video_id"] == "BddP6PYo2gs"
    assert "embed" in res["embed_url"]

def test_detect_open_website_human_like():
    os_engine = VoiceOSActions()
    res1 = os_engine.detect_and_handle_os_action("can u open youtube")
    assert res1 is not None
    assert res1["action"] == "open_website"
    assert res1["url"] == "https://www.youtube.com"

    # With question mark and capital letters
    res1_q = os_engine.detect_and_handle_os_action("can you open YouTube?")
    assert res1_q is not None
    assert res1_q["action"] == "open_website"
    assert res1_q["url"] == "https://www.youtube.com"

    res2 = os_engine.detect_and_handle_os_action("open drive")
    assert res2 is not None
    assert res2["action"] == "open_website"
    assert res2["url"] == "https://drive.google.com"

    res3 = os_engine.detect_and_handle_os_action("open github please")
    assert res3 is not None
    assert res3["action"] == "open_website"
    assert res3["url"] == "https://github.com"

def test_detect_stop_audio():
    os_engine = VoiceOSActions()
    res = os_engine.detect_and_handle_os_action("silence stop playing")
    assert res is not None
    assert res["action"] == "stop_audio"
    assert res["status"] == "stopped"

def test_detect_standby_chained_actions():
    os_engine = VoiceOSActions()
    # Search command
    res_search = os_engine.detect_and_handle_os_action("search kesariya")
    assert res_search is not None
    assert res_search["action"] == "search"
    assert res_search["query"] == "kesariya"
    assert res_search["standby"] is True

    # Play command
    res_play = os_engine.detect_and_handle_os_action("play it")
    assert res_play is not None
    assert res_play["action"] == "play_youtube"
    assert res_play["standby"] is True

    # Pause command
    res_pause = os_engine.detect_and_handle_os_action("pause")
    assert res_pause is not None
    assert res_pause["action"] == "pause_resume"
    assert res_pause["standby"] is True

    # Close command
    res_close = os_engine.detect_and_handle_os_action("close it")
    assert res_close is not None
    assert res_close["action"] == "close_browser"
    assert res_close["standby"] is False

def test_detect_non_os_command():
    os_engine = VoiceOSActions()
    res = os_engine.detect_and_handle_os_action("Jarvis, scan payment_service.py AST for security bugs")
    assert res is None
