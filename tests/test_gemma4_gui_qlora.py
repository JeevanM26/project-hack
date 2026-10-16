"""
Unit tests for backend/finetune_gemma4_gui_qlora.py
Verifies QLoRA configuration, Gemma 4 token formatting, dataset schema, and dry-run manifest.
"""
import os
import sys
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from finetune_gemma4_gui_qlora import (
    CANONICAL_GUI_TRAJECTORIES,
    format_gemma4_trajectory_chat,
    inspect_gpu_hardware,
    train_gemma4_gui_qlora,
    DEFAULT_DATASET_PATH
)

def test_canonical_trajectories_structure():
    assert len(CANONICAL_GUI_TRAJECTORIES) >= 5
    for traj in CANONICAL_GUI_TRAJECTORIES:
        assert "turn_id" in traj
        assert "instruction" in traj
        assert "actions" in traj
        assert "state_update" in traj
        assert len(traj["actions"]) > 0

def test_gemma4_special_tokens_formatting():
    sample = CANONICAL_GUI_TRAJECTORIES[0]
    formatted = format_gemma4_trajectory_chat(sample)
    assert "<start_of_turn>user" in formatted
    assert "<end_of_turn>" in formatted
    assert "<start_of_turn>model" in formatted
    assert "<|think|>" in formatted
    assert "<|plan|>" in formatted

def test_rtx5060_hardware_profile():
    hw = inspect_gpu_hardware(dry_run=True)
    assert hw["cuda_available"] is True
    assert "RTX 5060" in hw["device_name"]
    assert hw["vram_gb"] == 8.0
    assert hw["recommended_precision"] == "bfloat16"

def test_dry_run_training_produces_adapter_config(tmp_path):
    out_dir = str(tmp_path / "adapters")
    summary = train_gemma4_gui_qlora(
        base_model_id="google/gemma-4-E4B-it",
        output_dir=out_dir,
        dry_run=True
    )
    assert summary["status"] == "COMPLETED"
    assert summary["rank"] == 16
    assert summary["alpha"] == 32
    assert "q_proj" in summary["target_modules"]

    manifest_file = os.path.join(out_dir, "adapter_config.json")
    assert os.path.exists(manifest_file)
    with open(manifest_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["base_model"] == "google/gemma-4-E4B-it"
    assert data["adapter_type"] == "QLoRA_NF4"
