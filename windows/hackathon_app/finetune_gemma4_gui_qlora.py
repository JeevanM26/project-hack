# Unsloth / TRL QLoRA Fine-Tuning Script for Gemma 4 GUI & AST Swarm Trajectories (`gui_trajectories.jsonl`)
# Optimized for NVIDIA RTX 5060 (8GB VRAM + 24GB System RAM)
import json
from pathlib import Path

DATASET_PATH = Path('./gui_trajectories.jsonl')
rows = [json.loads(l) for l in DATASET_PATH.read_text().splitlines() if l.strip()] if DATASET_PATH.exists() else []
print(f'[J.A.R.V.I.S. QLoRA] Loaded {len(rows)} real GUI & Swarm trajectories')
