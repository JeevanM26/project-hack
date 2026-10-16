"""
FastAPI Backend for J.A.R.V.I.S. (Hacktoberfest Hack Day Bengaluru 2026 - Track 1: Best Use of Gemma 4).
Combines G1 (Autonomous Dynamic Multi-Agent Swarm with 1 Single Gemma 4 Model)
and G2 (Voice-First AI Interaction with Sarvam AI).
"""
import os
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents import JarvisMultiAgentSwarm
from sarvam_voice import SarvamVoicePipeline

app = FastAPI(
    title="J.A.R.V.I.S. Gemma 4 + Sarvam AI Multi-Agent OS",
    description="Single-Model Dynamic Agent Swarm & Voice Command Center for Open-Source Maintainers"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REPO_DIR = os.getenv("JARVIS_REPO_DIR", os.path.join(os.path.dirname(__file__), "sample_repo"))
swarm = JarvisMultiAgentSwarm(repo_dir=REPO_DIR)
voice = SarvamVoicePipeline()


class CommandRequest(BaseModel):
    command: str
    language_code: str = "en-IN"
    synthesize_voice: bool = True
    simulate_hallucination: bool = False


@app.get("/api/status")
def get_system_status():
    """Returns active Gemma 4 single-model config and Sarvam voice pipeline state."""
    return {
        "status": "online",
        "single_model": swarm.engine.model_name,
        "repo_dir": REPO_DIR,
        "indexed_modules": list(swarm.grounding.build_index().keys()),
        "sarvam_configured": bool(voice.api_key),
        "gemini_api_configured": bool(swarm.engine.gemini_api_key),
    }


@app.get("/api/index")
def get_repo_index():
    """Returns the deterministic AST symbol index of the project."""
    return {"repo_dir": REPO_DIR, "index": swarm.grounding.build_index()}


@app.get("/api/blackboard")
def get_current_blackboard():
    """Returns the live Shared Project Blackboard state."""
    bb = swarm.current_blackboard
    if not bb:
        return {"status": "idle", "message": "No active mission on blackboard"}
    return {
        "status": "active",
        "objective": bb.objective,
        "blueprint": bb.blueprint,
        "active_agents": bb.active_agents,
        "chat_bus": bb.chat_bus,
        "files_registered": list(bb.files_registry.keys()),
        "receipts": bb.verification_receipts
    }


@app.post("/api/mission")
def run_text_or_transcribed_mission(req: CommandRequest):
    """
    Runs the single-model dynamic multi-agent swarm:
    Handles YouTube playback, project building, or AST-grounded bug triage.
    """
    result = swarm.execute_voice_mission(
        req.command,
        simulate_hallucination=req.simulate_hallucination
    )
    
    if req.synthesize_voice and voice.api_key:
        try:
            tts = voice.synthesize_speech(result["spoken_response"], language_code=req.language_code)
            result["tts_audio"] = tts
        except Exception as e:
            result["tts_warning"] = str(e)

    return result


@app.post("/api/voice-mission")
async def run_audio_mission(
    audio: UploadFile = File(...),
    language_code: str = Form("en-IN"),
    mode: str = Form("codemix"),
    simulate_hallucination: bool = Form(False),
):
    """
    Accepts raw microphone audio from user, transcribes via Sarvam Saaras v4,
    executes single-model Gemma 4 swarm, and synthesizes audio via Sarvam Bulbul v4 Flash.
    """
    audio_bytes = await audio.read()
    repo_files = list(swarm.grounding.build_index().keys())
    
    stt_res = voice.transcribe_speech(
        audio_bytes=audio_bytes,
        filename=audio.filename or "command.wav",
        mode=mode,
        language_code=language_code,
        keyterms=repo_files + ["pytest", "idempotency", "GST", "webhook", "Gemma", "YouTube", "Kesariya"],
    )
    
    mission_res = swarm.execute_voice_mission(
        stt_res["transcript"],
        simulate_hallucination=simulate_hallucination
    )
    
    tts_res = None
    if voice.api_key:
        try:
            tts_res = voice.synthesize_speech(mission_res["spoken_response"], language_code=language_code)
        except Exception:
            pass

    return {
        "stt": stt_res,
        "mission": mission_res,
        "tts": tts_res,
    }


@app.get("/api/os-action/youtube")
def trigger_youtube_action(query: str = Query("Kesariya Brahmastra")):
    """Direct testing endpoint for YouTube song playback action."""
    return swarm.os_actions.play_youtube_song(query, auto_open_browser=False)
