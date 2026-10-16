import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from hardware_profile import HardwareOptimizer

def test_rtx5060_hardware_telemetry():
    hw = HardwareOptimizer()
    telemetry = hw.get_hardware_telemetry()

    assert telemetry["gpu"]["name"] == "NVIDIA GeForce RTX 5060"
    assert telemetry["gpu"]["vram_total_gb"] == 8.0
    assert telemetry["ram"]["total_gb"] == 24.0
    assert telemetry["recommended_model"]["id"] == "gemma-4-12b-it"
    assert telemetry["gpu"]["gpu_offload_percentage"] > 90.0

def test_modelfile_generation():
    hw = HardwareOptimizer()
    modelfile_text = hw.generate_ollama_modelfile()

    assert "FROM gemma4:12b" in modelfile_text
    assert "PARAMETER num_gpu 36" in modelfile_text
    assert "PARAMETER num_ctx 8192" in modelfile_text
