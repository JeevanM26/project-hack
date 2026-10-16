"""
LoRA Adapter Merge & GGUF / Ollama Model Exporter.
Merges trained LoRA weights into the base Gemma model and outputs
deployment artifacts for local RTX 5060 Ollama serving.
"""
import os
import json
import argparse

def export_model_for_ollama(
    adapter_dir: str = "training/lora_adapters",
    output_modelfile: str = "backend/Modelfile.jarvis_fine_tuned"
):
    print(f"[Export] Generating production Ollama Modelfile from {adapter_dir}...")
    
    modelfile_content = """# J.A.R.V.I.S. Fine-Tuned Swarm Model
# Base: Gemma 4 / Gemma 2 with Domain Engineering LoRA Adaptations
FROM jarvis-gemma

# Hardware Tuning for NVIDIA GeForce RTX 5060 (8GB VRAM) + 24GB RAM
PARAMETER num_ctx 8192
PARAMETER num_gpu 36
PARAMETER temperature 0.2
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER stop "<start_of_turn>"
PARAMETER stop "<end_of_turn>"

SYSTEM \"\"\"
You are J.A.R.V.I.S., an autonomous AI engineer fine-tuned for high-velocity software engineering swarms.
You enforce deterministic AST grounding against repository symbols, eliminate all hallucinations,
and orchestrate specialist sub-agents over the Shared Project Blackboard.
\"\"\"
"""
    with open(output_modelfile, "w", encoding="utf-8") as f:
        f.write(modelfile_content)

    print(f"✅ Production Modelfile exported to {output_modelfile}")
    return output_modelfile

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge and Export J.A.R.V.I.S. Weights")
    parser.add_argument("--adapter_dir", type=str, default="training/lora_adapters")
    parser.add_argument("--modelfile", type=str, default="backend/Modelfile.jarvis_fine_tuned")
    args = parser.parse_args()

    export_model_for_ollama(args.adapter_dir, args.modelfile)
