"""
AirLLM Layer-Wise Model Runner & Inference Bridge
Runs massive LLMs (Gemma, Llama, Qwen, Mixtral) on consumer hardware by streaming layers dynamically.

Usage:
    python backend/airllm_demo.py --prompt "Explain quantum computing in simple terms."
    python backend/airllm_demo.py --model "google/gemma-2-9b-it" --compression 4bit
"""

import argparse
import sys
import time
import torch


def run_airllm_inference(
    model_name: str = "google/gemma-2-9b-it",
    prompt: str = "Explain what makes Google Gemma 2 unique and powerful.",
    compression: str = "4bit",
    max_new_tokens: int = 150,
    hf_token: str = None,
):
    print("=" * 70)
    print("AIR-LLM LAYER-WISE STREAMING INFERENCE")
    print(f"Target Model:  {model_name}")
    print(f"Compression:   {compression or 'None (FP16)'}")
    print(f"CUDA Available:{torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU Device:    {torch.cuda.get_device_name(0)}")
        print(f"Total VRAM:    {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
    print("=" * 70)

    try:
        from airllm import AutoModel
    except ImportError:
        print("[ERROR] airllm is not installed. Run: pip install airllm")
        sys.exit(1)

    print(f"\n[1/3] Initializing AirLLM AutoModel for '{model_name}'...")
    start_time = time.time()

    kwargs = {}
    if compression:
        kwargs["compression"] = compression
    if hf_token:
        kwargs["hf_token"] = hf_token

    try:
        model = AutoModel.from_pretrained(model_name, **kwargs)
        init_time = time.time() - start_time
        print(f"[OK] Model initialized in {init_time:.2f}s")
    except Exception as e:
        print(f"[FAILED] Could not load model '{model_name}': {e}")
        print("\nNote: For gated Hugging Face models like 'google/gemma-2-9b-it', ensure you have")
        print("accepted Google's terms on HuggingFace and provide your HF token via:")
        print("  python backend/airllm_demo.py --token <YOUR_HF_TOKEN>")
        return

    print(f"\n[2/3] Tokenizing prompt: \"{prompt}\"...")
    input_tokens = model.tokenizer(
        [prompt],
        return_tensors="pt",
        return_attention_mask=False,
        truncation=True,
        max_length=512,
        padding=False,
    )

    print("\n[3/3] Generating output via layer-by-layer streaming...")
    gen_start = time.time()
    device_id = "cuda:0" if torch.cuda.is_available() else "cpu"
    generation_output = model.generate(
        input_tokens["input_ids"].to(device_id),
        max_new_tokens=max_new_tokens,
        use_cache=True,
        return_dict_in_generate=True,
    )
    gen_time = time.time() - gen_start

    result_text = model.tokenizer.decode(generation_output.sequences[0], skip_special_tokens=True)
    print("\n" + "=" * 70)
    print("GENERATED RESULT:")
    print("=" * 70)
    print(result_text)
    print("=" * 70)
    print(f"Generation completed in {gen_time:.2f}s (~{max_new_tokens / max_time:.1f} tok/s)" if (max_time := max(0.01, gen_time)) else "")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AirLLM Gemma Runner")
    parser.add_argument("--model", type=str, default="google/gemma-2-9b-it", help="HuggingFace model ID or local path")
    parser.add_argument("--prompt", type=str, default="Write a python function to compute the Fibonacci sequence efficiently.", help="Input prompt")
    parser.add_argument("--compression", type=str, default="4bit", choices=["4bit", "8bit", "none"], help="Block compression")
    parser.add_argument("--tokens", type=int, default=128, help="Max new tokens")
    parser.add_argument("--token", type=str, default=None, help="Hugging Face API token if model is gated")

    args = parser.parse_args()
    comp = None if args.compression == "none" else args.compression
    run_airllm_inference(
        model_name=args.model,
        prompt=args.prompt,
        compression=comp,
        max_new_tokens=args.tokens,
        hf_token=args.token,
    )
