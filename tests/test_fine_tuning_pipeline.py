import os
import sys
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "training")))
from merge_and_export import export_model_for_ollama

def test_instruction_dataset_exists_and_valid():
    dataset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "training", "dataset.jsonl"))
    assert os.path.exists(dataset_path)
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    assert len(lines) >= 5
    for line in lines:
        data = json.loads(line)
        assert "instruction" in data
        assert "response" in data

def test_benchmark_results_scorecard():
    results_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "training", "benchmark_results.json"))
    assert os.path.exists(results_path)
    
    with open(results_path, "r", encoding="utf-8") as f:
        scorecard = json.load(f)
    
    assert scorecard["ast_grounding_rate"] == 100.0
    assert scorecard["json_compliance_rate"] == 100.0
    assert scorecard["intent_accuracy"] == 100.0

def test_export_modelfile():
    out_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "Modelfile.jarvis_fine_tuned"))
    res = export_model_for_ollama(output_modelfile=out_file)
    assert os.path.exists(res)
