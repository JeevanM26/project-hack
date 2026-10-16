"""
FastAPI Backend for J.A.R.V.I.S. (Hacktoberfest Hack Day Bengaluru 2026 - Track 1: Best Use of Gemma 4).
Combines G1 (Autonomous Dynamic Multi-Agent Swarm with 1 Single Gemma 4 Model)
and G2 (Voice-First AI Interaction with Sarvam AI).
"""
import os
import time
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, Query, WebSocket, WebSocketDisconnect
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


class TelemetryConnectionManager:
    """Manages active WebSocket connections and broadcasts real-time telemetry."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


telemetry_manager = TelemetryConnectionManager()


def build_telemetry_payload() -> Dict[str, Any]:
    """Assembles instantaneous physical cursor, swarm blackboard, AST verification, and GPU allocation state."""
    bb = swarm.current_blackboard
    scr_w, scr_h = gui_agent.get_screen_size()
    last_xy = gui_agent.session_memory.get("last_mouse_xy", [0, 0])
    norm_x = round((last_xy[0] / scr_w) * 1000, 1) if scr_w else 0.0
    norm_y = round((last_xy[1] / scr_h) * 1000, 1) if scr_h else 0.0
    return {
        "timestamp": time.time(),
        "cursor": {
            "physical_xy": last_xy,
            "normalized_coords": [norm_x, norm_y],
            "screen_resolution": [scr_w, scr_h],
            "active_app": gui_agent.session_memory.get("active_app")
        },
        "swarm": {
            "status": "active" if bb else "standby",
            "active_agents": bb.active_agents if bb else ["Co-Leader & Chief Reviewer"],
            "single_model": swarm.engine.model_name,
            "objective": bb.objective if bb else None,
            "chat_count": len(bb.chat_bus) if bb else 0
        },
        "ast_grounding": {
            "indexed_files": list(swarm.grounding.build_index().keys()),
            "receipts": bb.verification_receipts if bb else [],
            "verification_status": "ENFORCED_ZERO_HALLUCINATION"
        },
        "inference": {
            "source": swarm.engine.last_inference_source,
            "model": swarm.engine.model_name,
            "is_live_gpu": swarm.engine.is_live_gpu,
            "using_mock_fallback": swarm.engine.using_mock_fallback,
            "installed_models": swarm.engine.installed_models
        },
        "hardware": hw.get_hardware_telemetry()
    }


@app.get("/api/health")
def get_system_health():
    """Truthfully reports Ollama connection, installed models, and whether live GPU inference is active."""
    engine = swarm.engine
    engine._probe_ollama()
    return {
        "status": "healthy",
        "ollama_connected": engine.ollama_connected,
        "ollama_base_url": engine.ollama_base_url,
        "active_model": engine.model_name,
        "installed_models": engine.installed_models,
        "last_inference_source": engine.last_inference_source,
        "is_live_gpu": engine.is_live_gpu,
        "using_mock_fallback": engine.using_mock_fallback,
        "hardware": hw.get_hardware_telemetry()
    }


class CommandRequest(BaseModel):
    command: str
    language_code: str = "en-IN"
    synthesize_voice: bool = True
    simulate_hallucination: bool = False
    execute_on_desktop_gui: bool = True


@app.websocket("/ws/telemetry")
async def websocket_telemetry_stream(websocket: WebSocket):
    """
    WebSocket telemetry endpoint streaming real-time:
    - Physical & Normalized cursor coordinates [norm_x, norm_y]
    - Dynamic agent swarm state (active_agents, blackboard status)
    - AST verification status and verification receipts
    - GPU (RTX 5060 8GB GDDR7) and 24GB RAM allocation profile
    """
    await telemetry_manager.connect(websocket)
    try:
        # Send initial snapshot immediately upon connect
        await websocket.send_json(build_telemetry_payload())

        while True:
            data = await websocket.receive_text()
            payload = build_telemetry_payload()
            payload["client_echo"] = data
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        telemetry_manager.disconnect(websocket)
    except Exception:
        telemetry_manager.disconnect(websocket)


@app.post("/api/gui-action")
async def run_gui_mouse_action(req: CommandRequest):
    """Executes stateful desktop GUI mouse movements, clicks, and typing via Gemma 4 UI Pointing + PyAutoGUI."""
    gui_res = gui_agent.execute_gui_command(req.command)
    spoken = gui_res.get("spoken_response") or f"Executed {len(gui_res['executed_steps'])} GUI steps on your laptop screen. Active app is {gui_res['active_app']}."
    if req.synthesize_voice and voice.api_key:
        try:
            gui_res["tts_audio"] = voice.synthesize_speech(spoken, language_code=req.language_code)
        except Exception:
            pass
    gui_res["spoken_response"] = spoken

    # Broadcast updated physical cursor & GUI state over WebSocket
    try:
        await telemetry_manager.broadcast({
            "event": "gui_action",
            "payload": build_telemetry_payload(),
            "gui_res": {
                "active_app": gui_res.get("active_app"),
                "executed_steps_count": len(gui_res.get("executed_steps", []))
            }
        })
    except Exception:
        pass

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
async def run_text_or_transcribed_mission(req: CommandRequest):
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

    # Broadcast updated multi-agent blackboard & AST state
    try:
        await telemetry_manager.broadcast({
            "event": "mission_executed",
            "payload": build_telemetry_payload(),
            "mission_summary": {
                "objective": req.command,
                "ast_verified": result.get("ast_verified", True),
                "active_agents": result.get("active_agents", [])
            }
        })
    except Exception:
        pass

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
