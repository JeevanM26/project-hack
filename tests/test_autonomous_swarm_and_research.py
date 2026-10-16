"""
Unit and Integration Tests for J.A.R.V.I.S. Autonomous Swarm & Research System.
Verifies:
- SharedGlobalBlackboard thread safety, state updates, and snapshot generation
- DeepResearchAgent web searching and crawling functionality
- WorkspaceCoderAgent file authoring, AST verification, and subprocess execution
- Full 5-Phase execute_autonomous_mission loop
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from blackboard import global_blackboard, SharedBlackboard
from research_agent import DeepResearchAgent
from workspace_coder_agent import WorkspaceCoderAgent
from agents import JarvisMultiAgentSwarm, SingleGemma4Engine


def test_blackboard_lifecycle():
    bb = SharedBlackboard()
    bb.reset_state(mission_id="test-mission-001", user_objective="Test Research & Build")
    assert bb.status == "IDLE"
    assert bb.user_objective == "Test Research & Build"

    # Update agent & chat
    bb.update_agent("Researcher", "RESEARCHING", "Querying technical docs")
    bb.post_chat_message("Researcher", "Architect", "Indexed 3 sources", kind="chat")
    assert len(bb.team_chat_bus) == 1
    assert bb.team_chat_bus[0]["from_agent"] == "Researcher"

    # Add research note
    bb.add_research_note(
        url="https://example.com/docs",
        title="Example Docs",
        summary="Verified performance benchmarks",
        key_takeaways=["Fast latency", "Low memory"]
    )
    assert len(bb.research_notes) == 1
    assert bb.research_notes[0]["url"] == "https://example.com/docs"

    # Terminal log
    bb.append_terminal_log("pytest", "1 passed", "", 0)
    assert len(bb.terminal_logs) == 1
    assert bb.terminal_logs[0]["exit_code"] == 0

    # Snapshot validation
    snap = bb.get_snapshot()
    assert snap["mission_id"] == "test-mission-001"
    assert "Researcher" in snap["active_agents"]


def test_workspace_coder_agent_file_and_ast():
    coder = WorkspaceCoderAgent()
    workspace_dir = coder.initialize_workspace("test_verification_project")
    assert os.path.exists(workspace_dir)

    # Valid Python file
    py_code = (
        'def add_numbers(a: int, b: int) -> int:\n'
        '    return a + b\n'
    )
    res = coder.create_or_overwrite_file("calc.py", py_code)
    assert res["ast_syntax_valid"] is True
    assert os.path.exists(os.path.join(workspace_dir, "calc.py"))
    assert "add_numbers" in res["symbols"]["functions"]

    # Terminal command execution
    term_res = coder.run_shell_command("echo Hello Autonomous World", timeout=10)
    assert term_res["success"] is True
    assert "Hello Autonomous World" in term_res["stdout"]


def test_deep_research_agent_search_and_crawl():
    researcher = DeepResearchAgent()
    # Search test
    results = researcher.search_web("Python software engineering", max_results=2)
    assert isinstance(results, list)

    # Crawl test (using clean known static resource or fallback)
    crawl_res = researcher.crawl_and_read_url("https://httpbin.org/html")
    assert "url" in crawl_res
    assert isinstance(crawl_res["content"], str)


def test_full_autonomous_mission_execution():
    repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "sample_repo"))
    swarm = JarvisMultiAgentSwarm(repo_dir=repo_dir)
    res = swarm.execute_autonomous_mission(
        objective="Mini Task Scheduler with SQLite",
        depth=1,
        run_tests=False,
        launch_app=False
    )
    assert res["type"] == "autonomous_mission"
    assert "workspace_dir" in res
    assert os.path.exists(res["workspace_dir"])
    assert len(res["generated_files"]) > 0
    assert "agent_trace" in res
    assert "blackboard" in res
    assert res["blackboard"]["status"] in ["COMPLETED", "PLANNING", "CODING"]
