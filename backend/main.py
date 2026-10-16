"""
FastAPI Backend for J.A.R.V.I.S. (Hacktoberfest Hack Day Bengaluru 2026 - Track 1: Best Use of Gemma 4).
Combines G1 (Autonomous Dynamic Multi-Agent Swarm with 1 Single Gemma 4 Model)
and G2 (Voice-First AI Interaction with Sarvam AI).
"""
import os
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents import JarvisMultiAgentSwarm
from sarvam_voice import SarvamVoicePipeline
from hardware_profile import HardwareOptimizer
from gui_computer_agent import JarvisGUIComputerAgent

app = FastAPI(
    title="J.A.R.V.I.S. Mark LXXXV — Gemma 4 GUI + Multi-Agent + Sarvam Voice OS",
    description="Single-Model Dynamic Agent Swarm & Physical Mouse GUI Operator for Open-Source Maintainers"
)

INDEX_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "jarvis_command_center.html"))
if not os.path.exists(INDEX_PATH):
    INDEX_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "index.html"))
if not os.path.exists(INDEX_PATH):
    INDEX_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "index.html"))

@app.get("/")
@app.head("/")
def serve_jarvis_frontend():
    """Serves the 3D J.A.R.V.I.S. Mark LXXXV Holographic Command Center UI."""
    return FileResponse(INDEX_PATH)

@app.get("/jarvis_command_center.html")
def serve_command_center():
    return FileResponse(INDEX_PATH)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REPO_DIR = os.getenv("JARVIS_REPO_DIR", os.path.join(os.path.dirname(__file__), "sample_repo"))
swarm = JarvisMultiAgentSwarm(repo_dir=REPO_DIR)
voice = SarvamVoicePipeline()
hw = HardwareOptimizer()
gui_agent = JarvisGUIComputerAgent()


class CommandRequest(BaseModel):
    command: str
    language_code: str = "en-IN"
    synthesize_voice: bool = True
    simulate_hallucination: bool = False
    execute_on_desktop_gui: bool = True


@app.post("/api/gui-action")
def run_gui_mouse_action(req: CommandRequest):
    """Executes stateful desktop GUI mouse movements, clicks, and typing via Gemma 4 UI Pointing + PyAutoGUI."""
    gui_res = gui_agent.execute_gui_command(req.command)
    spoken = gui_res.get("spoken_response") or f"Executed {len(gui_res['executed_steps'])} GUI steps on your laptop screen. Active app is {gui_res['active_app']}."
    if req.synthesize_voice and voice.api_key:
        try:
            gui_res["tts_audio"] = voice.synthesize_speech(spoken, language_code=req.language_code)
        except Exception:
            pass
    gui_res["spoken_response"] = spoken
    return gui_res


@app.post("/api/stop")
@app.get("/api/stop")
def stop_all_active_media():
    """Immediately silences all background audio and kills automated browser processes."""
    return swarm.os_actions.stop_all_media()


@app.get("/api/telemetry")
def get_hardware_telemetry():
    """Returns real-time GPU (RTX 5060 8GB) and 24GB RAM allocation profile."""
    return hw.get_hardware_telemetry()


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
        "hardware": hw.get_hardware_telemetry(),
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

    if req.execute_on_desktop_gui:
        try:
            result["gui_trace"] = gui_agent.execute_gui_command(req.command)
        except Exception as e:
            result["gui_trace_warning"] = str(e)
    
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


@app.get("/api/browser-status")
def get_browser_automation_status():
    """Returns active Playwright desktop browser session state."""
    if swarm.os_actions.browser_auto:
        return swarm.os_actions.browser_auto.get_status()
    return {"standby": False, "active_app": None, "worker_status": {"is_alive": False}}


class BrowserActionRequest(BaseModel):
    action: str  # open, search, play, pause, close
    query: Optional[str] = None
    url: Optional[str] = None
    app_name: Optional[str] = "browser"


@app.post("/api/browser-action")
def trigger_browser_action(req: BrowserActionRequest):
    """Direct GUI control endpoint for Playwright browser automation."""
    auto = swarm.os_actions.browser_auto
    if not auto:
        return {"success": False, "error": "Browser automation not initialized"}

    if req.action == "open" and req.url:
        return auto.open_website(req.url, req.app_name or "browser")
    elif req.action == "search" and req.query:
        return auto.search(req.query)
    elif req.action in ["play", "play_video"]:
        return auto.play_video(req.query)
    elif req.action in ["pause", "pause_resume"]:
        return auto.pause_resume()
    elif req.action == "close":
        return auto.close_active()
    else:
        return {"success": False, "error": f"Unsupported browser action: {req.action}"}
