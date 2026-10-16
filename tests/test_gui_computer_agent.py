import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from gui_computer_agent import JarvisGUIComputerAgent


def test_gui_agent_screen_dimensions():
    agent = JarvisGUIComputerAgent()
    w, h = agent.get_screen_size()
    assert w > 0
    assert h > 0


def test_gui_agent_normalized_coordinate_mapping():
    agent = JarvisGUIComputerAgent()
    res = agent.move_and_click_visibly(norm_x=310, norm_y=52, duration=0.1, click=False)
    assert 0 <= res["pixel_x"] <= res["screen_w"]
    assert 0 <= res["pixel_y"] <= res["screen_h"]
    assert res["norm_x"] == 310
    assert res["norm_y"] == 52


def test_gui_agent_turn_1_open_youtube():
    agent = JarvisGUIComputerAgent()
    res = agent.execute_gui_command("Jarvis, open YouTube")
    assert res["turn"] == 1
    assert res["active_app"] == "browser_youtube"
    assert res["session_state"]["youtube_open"] is True
    assert len(res["executed_steps"]) >= 2


def test_gui_agent_turn_2_search_and_play_believer():
    agent = JarvisGUIComputerAgent()
    # Turn 1
    agent.execute_gui_command("Jarvis, open YouTube")
    # Turn 2
    res = agent.execute_gui_command("Can you search for Believer")
    assert res["turn"] == 2
    assert "Believer" in res["display_title"]
    assert res["active_app"] == "browser_youtube_playing"
    assert "7wtfhZwyrcc" in res["watch_url"]
    assert len(res["executed_steps"]) >= 3


def test_gui_agent_turn_2_search_kesariya():
    agent = JarvisGUIComputerAgent()
    res = agent.execute_gui_command("play kesariya on youtube")
    assert res["turn"] == 2
    assert "Kesariya" in res["display_title"]
    assert "BddP6PYo2gs" in res["watch_url"]


def test_gui_agent_close():
    agent = JarvisGUIComputerAgent()
    agent.session_memory["youtube_open"] = True
    res = agent.execute_gui_command("Jarvis, close browser")
    assert res["action"] == "close"
    assert res["active_app"] == "desktop"
    assert res["session_state"]["youtube_open"] is False
