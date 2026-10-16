import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from agents import SingleGemma4Engine, JarvisMultiAgentSwarm

def test_single_gemma_engine_initialization():
    engine = SingleGemma4Engine()
    assert engine.model_name in ["jarvis-gemma", "gemma:2b", "gemma-4-12b-it"]
    assert engine.ollama_base_url == "http://localhost:11434/v1"

def test_single_gemma_engine_role_execution():
    engine = SingleGemma4Engine()
    res = engine.call_agent("Co-Leader", "Review mission status", "Check all active agents")
    assert isinstance(res, dict)
    assert "role" in res or "status" in res

def test_swarm_execute_mission_ast_grounding():
    repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "sample_repo"))
    swarm = JarvisMultiAgentSwarm(repo_dir=repo_dir)
    res = swarm.execute_voice_mission("Refactor payment idempotency in payment_service.py")
    assert res["type"] == "repo_triage"
    assert res["target_file"] == "payment_service.py"
    assert res["verification_receipt"]["ast_syntax_valid"] is True
    assert "agent_trace" in res
    assert "blackboard" in res
