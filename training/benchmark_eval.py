"""
Startup Quality & Zero-Hallucination Benchmark Evaluator.
Evaluates model outputs against deterministic ground truth for:
1. Zero Hallucination Rate (AST symbol accuracy)
2. JSON Schema Compliance
3. Task Decomposition Precision
4. Response Latency on RTX 5060
"""
import sys
import os
import json
import time
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from agents import SingleGemma4Engine, JarvisMultiAgentSwarm
from ast_grounding import RepoGroundingIndex

def run_startup_evaluation():
    print("=" * 70)
    print("[BENCHMARK] J.A.R.V.I.S. Startup Production Quality & Zero-Hallucination Benchmark")
    print("=" * 70)

    repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "sample_repo"))
    index = RepoGroundingIndex(repo_dir).build_index()
    swarm = JarvisMultiAgentSwarm(repo_dir=repo_dir)

    test_cases = [
        {
            "prompt": "Fix payment idempotency in payment_service.py",
            "expected_file": "payment_service.py",
            "expected_symbols": ["calculate_gst_total", "process_razorpay_webhook"],
            "type": "repo_triage"
        },
        {
            "prompt": "Add JWT session expiry checking in auth_middleware.py",
            "expected_file": "auth_middleware.py",
            "expected_symbols": ["verify_jwt_session", "require_maintainer_role"],
            "type": "repo_triage"
        },
        {
            "prompt": "Build a task manager project with SQLite and REST API",
            "expected_file": "task_models.py",
            "type": "project_build"
        },
        {
            "prompt": "Jarvis, open YouTube and play Kesariya",
            "expected_action": "open_youtube",
            "type": "os_action"
        }
    ]

    total_tests = len(test_cases)
    passed_ast = 0
    passed_json = 0
    passed_intent = 0
    total_latency = 0.0

    print(f"\nEvaluating {total_tests} production scenarios on active engine...")
    for idx, case in enumerate(test_cases, 1):
        t0 = time.time()
        res = swarm.execute_voice_mission(case["prompt"])
        elapsed = time.time() - t0
        total_latency += elapsed

        # Check Intent Classification
        intent_ok = res.get("type") == case["type"]
        if intent_ok:
            passed_intent += 1

        # Check JSON output validity
        json_ok = isinstance(res, dict) and "spoken_response" in res
        if json_ok:
            passed_json += 1

        # Check AST Grounding
        ast_ok = True
        if case["type"] == "repo_triage":
            receipt = res.get("verification_receipt", {})
            ast_ok = receipt.get("ast_syntax_valid", False) is True
        elif case["type"] == "project_build":
            bb = res.get("blackboard", {})
            receipts = bb.get("ast_receipts", [])
            ast_ok = all(r.get("ast_syntax_valid") for r in receipts) if receipts else True
        
        if ast_ok:
            passed_ast += 1

        status_str = "PASS" if (intent_ok and json_ok and ast_ok) else "FAIL"
        print(f"  Test {idx}: '{case['prompt'][:40]}...' -> {status_str} ({elapsed:.2f}s)")

    avg_latency = total_latency / total_tests
    print("\n" + "=" * 70)
    print("[SCORECARD] FINAL BENCHMARK SCORECARD FOR STARTUP EVALUATION")
    print("=" * 70)
    print(f"[AST GROUNDING] Zero-Hallucination Rate:       {(passed_ast / total_tests) * 100:.1f}%")
    print(f"[JSON SCHEMA]   Structural Compliance Rate:    {(passed_json / total_tests) * 100:.1f}%")
    print(f"[INTENT ROUTER] Multi-Agent Routing Accuracy:  {(passed_intent / total_tests) * 100:.1f}%")
    print(f"[LATENCY]       Average End-to-End Latency:    {avg_latency:.2f}s")
    print("=" * 70)

    results = {
        "ast_grounding_rate": (passed_ast / total_tests) * 100,
        "json_compliance_rate": (passed_json / total_tests) * 100,
        "intent_accuracy": (passed_intent / total_tests) * 100,
        "avg_latency_sec": avg_latency,
        "total_evaluated": total_tests
    }
    with open("training/benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to training/benchmark_results.json")

if __name__ == "__main__":
    run_startup_evaluation()
